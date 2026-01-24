"""Repository ingestion API endpoints."""

import logging
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path

from app.core.session import session_manager
from app.ingestion.github_loader import load_github_repo, cleanup_repo_directory, get_repo_structure
from app.ingestion.filters import filter_repository_files, read_file_content
from app.ingestion.chunker import chunk_file_content
from app.ingestion.manifest import generate_repo_manifest
from app.vector.chroma import ChromaClient

logger = logging.getLogger(__name__)
router = APIRouter()
chroma_client = ChromaClient()


import asyncio
from datetime import datetime

class IngestRequest(BaseModel):
    """Request model for repository ingestion."""
    repo_url: str
    user_id: str = "demo-user"


class IngestResponse(BaseModel):
    """Response model for repository ingestion."""
    session_id: str
    status: str
    files_processed: int
    chunks_created: int
    manifest: Dict[str, Any]
    vector_status: Optional[str] = None


from app.core.auth import get_current_user, TokenData
from fastapi import Depends

@router.post("", response_model=IngestResponse)
async def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks, user: TokenData = Depends(get_current_user)):
    """
    Synchronous repository ingestion (Async Handler).
    Blocks until cloning, processing, and vector storage are complete.
    """
    session_id = None
    
    try:
        # Validate repo URL
        if not request.repo_url or not request.repo_url.strip():
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        logger.info(f"Starting ingestion for repo: {request.repo_url}")
        
        # Step 1: Create session
        session_id = session_manager.create_session(repo_url=request.repo_url)
        session_manager.update_session(session_id, status="cloning")
        logger.info(f"Created session: {session_id}")
        
        # --- Create Chat Record in MongoDB ---
        from app.db.mongo import get_mongo_client
        mongo_client = get_mongo_client()
        if mongo_client and mongo_client.is_connected():
            chat_data = {
                "chat_id": session_id,
                "user_id": request.user_id,
                "repo_url": request.repo_url,
                "repo_name": request.repo_url.split("/")[-1], # Simple guess
                "created_at": datetime.utcnow()
            }
            await mongo_client.create_chat(chat_data)
        
        # Step 2: Clone repository (Blocking IO in Thread)
        repo_path = None
        try:
            # Run blocking clone in thread
            repo_info = await asyncio.to_thread(load_github_repo, request.repo_url, session_id)
            repo_path = repo_info["repo_path"]
            session_manager.update_session(session_id, status="filtering", repo_path=repo_path)
            logger.info(f"Repository cloned: {repo_info['repo_name']}")
            
            # Update Chat with correct repo name now that we have it?
            # Optional, for now the initial guess or later update is fine.
        except ValueError as e:
            session_manager.update_session(session_id, status="failed")
            raise HTTPException(status_code=400, detail=f"Invalid repository URL: {str(e)}")
        except RuntimeError as e:
            session_manager.update_session(session_id, status="failed")
            raise HTTPException(status_code=413, detail=str(e))
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            logger.error(f"Failed to clone repository: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to clone repository: {str(e)}")
        
        # Step 3: Get file structure and filter files (IO Bound)
        try:
            file_list = get_repo_structure(repo_path)
            if not file_list:
                session_manager.update_session(session_id, status="failed")
                raise HTTPException(status_code=400, detail="Repository appears to be empty")
            
            repo_path_obj = Path(repo_path)
            filtered_files = filter_repository_files(repo_path_obj)
            
            if not filtered_files:
                session_manager.update_session(session_id, status="failed")
                raise HTTPException(status_code=400, detail="No processable files found")
            
            session_manager.update_session(session_id, status="processing", files_count=len(filtered_files))
            logger.info(f"Filtered {len(filtered_files)} files from {len(file_list)} total files")
        except HTTPException:
            raise
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            logger.error(f"Failed to filter files: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to process files: {str(e)}")
        
        # Step 4: Generate manifest
        try:
            manifest = generate_repo_manifest(repo_path, [str(f.relative_to(repo_path_obj)) for f in filtered_files])
            session_manager.store_manifest(session_id, manifest)
            session_manager.update_session(session_id, status="chunking")
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            logger.error(f"Failed to generate manifest: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to generate manifest: {str(e)}")
        
        # Step 5: Chunk files (CPU Bound - maybe strict async needed for very large repos, but ok for now)
        all_chunks = []
        files_processed = 0
        
        try:
            # We could offload heavy chunking to thread too
            def process_files():
                l_chunks = []
                l_processed = 0
                for file_path in filtered_files:
                    try:
                        content, is_summary = read_file_content(file_path)
                        if content is None: continue
                        relative_path = str(file_path.relative_to(repo_path_obj))
                        file_chunks = chunk_file_content(content, relative_path)
                        if file_chunks:
                            l_chunks.extend(file_chunks)
                            l_processed += 1
                    except Exception:
                        continue
                return l_chunks, l_processed

            all_chunks, files_processed = await asyncio.to_thread(process_files)
            
            if not all_chunks:
                session_manager.update_session(session_id, status="failed")
                raise HTTPException(status_code=500, detail="No chunks created from repository")
            
            # Store chunks in session
            session_manager.store_chunks(session_id, all_chunks)
            
            # Step 6: Store in ChromaDB
            try:
                # Chroma interactions might be simple enough to run in loop or offload if slow
                chroma_client.create_session_collection(session_id)
                # This was batched previously in Step 687, so it's safer now
                chroma_client.add_chunks(session_id, all_chunks)
                vector_status = "stored"
            except Exception as e:
                logger.error(f"Failed to store chunks in ChromaDB: {e}")
                vector_status = "failed"
            
            session_manager.update_session(
                session_id,
                status="completed",
                files_processed=files_processed,
                chunks_created=len(all_chunks)
            )
            
            logger.info(f"Ingestion completed: {files_processed} files, {len(all_chunks)} chunks")
            
        except HTTPException:
            raise
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            logger.error(f"Failed to chunk files: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")
        
        # Cleanup after response
        background_tasks.add_task(cleanup_repo_directory, session_id)
        
        return IngestResponse(
            session_id=session_id,
            status="completed",
            files_processed=files_processed,
            chunks_created=len(all_chunks),
            manifest=manifest,
            vector_status=vector_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        if session_id:
            session_manager.update_session(session_id, status="failed")
            # Attempt cleanup if session was created
            background_tasks.add_task(cleanup_repo_directory, session_id)
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")
        

@router.post("/{session_id}/resume", response_model=IngestResponse)
async def resume_repository_ingestion(session_id: str, request: IngestRequest, background_tasks: BackgroundTasks):
    """
    Resume/Re-ingest a repository for an existing session.
    Useful for restoring vector store context after server restart.
    """
    try:
        if not request.repo_url or not request.repo_url.strip():
             raise HTTPException(status_code=400, detail="Repository URL is required for re-ingestion")
             
        logger.info(f"Resuming ingestion for session: {session_id}, repo: {request.repo_url}")
        
        # We reuse the session ID but re-run the process
        # Update status
        session_manager.update_session(session_id, status="cloning")
        
        # Step 1: Clone (Async Thread)
        repo_path = None
        try:
            repo_info = await asyncio.to_thread(load_github_repo, request.repo_url, session_id)
            repo_path = repo_info["repo_path"]
            session_manager.update_session(session_id, status="filtering", repo_path=repo_path)
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            raise HTTPException(status_code=500, detail=f"Failed to clone: {str(e)}")
            
        # Step 2: Filter
        try:
            repo_path_obj = Path(repo_path)
            filtered_files = filter_repository_files(repo_path_obj)
            session_manager.update_session(session_id, status="processing", files_count=len(filtered_files))
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Failed to filter: {str(e)}")

        # Step 3: Manifest
        try:
            manifest = generate_repo_manifest(repo_path, [str(f.relative_to(repo_path_obj)) for f in filtered_files])
            session_manager.store_manifest(session_id, manifest)
        except Exception:
            pass # Non-critical

        # Step 4: Chunk & Vector Store
        # IMPORTANT: Vectors are ephemeral, so we treat it as fresh
        # But should we clear old collection first?
        try:
             chroma_client.delete_collection(session_id)
        except Exception:
             pass # Might not exist

        def process_files():
            l_chunks = []
            l_processed = 0
            for file_path in filtered_files:
                try:
                    content, is_summary = read_file_content(file_path)
                    if content is None: continue
                    relative_path = str(file_path.relative_to(repo_path_obj))
                    file_chunks = chunk_file_content(content, relative_path)
                    if file_chunks:
                        l_chunks.extend(file_chunks)
                        l_processed += 1
                except Exception:
                    continue
            return l_chunks, l_processed
            
        all_chunks, files_processed = await asyncio.to_thread(process_files)
        
        if all_chunks:
            session_manager.store_chunks(session_id, all_chunks)
            try:
                chroma_client.create_session_collection(session_id)
                chroma_client.add_chunks(session_id, all_chunks)
                vector_status = "stored"
            except Exception as e:
                logger.error(f"Failed to store vectors: {e}")
                vector_status = "failed"
        else:
             vector_status = "empty"

        session_manager.update_session(
            session_id,
            status="completed",
            files_processed=files_processed,
            chunks_created=len(all_chunks)
        )
        
        # Cleanup
        background_tasks.add_task(cleanup_repo_directory, session_id)
        
        return IngestResponse(
            session_id=session_id,
            status="completed",
            files_processed=files_processed,
            chunks_created=len(all_chunks),
            manifest=manifest if 'manifest' in locals() else {},
            vector_status=vector_status
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)}")
