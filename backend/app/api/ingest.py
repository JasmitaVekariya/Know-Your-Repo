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
    mode: str = "architect"  # architect, extension, system_design, debugger


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

async def run_ingestion_pipeline(session_id: str, repo_url: str, user_id: str, mode: str = "architect", background_tasks: BackgroundTasks = None):
    """
    Reusable ingestion pipeline.
    """
    try:
        # Step 1: Create/Update session
        if not session_manager.get_session(session_id):
             session_manager.create_session(repo_url=repo_url, session_id=session_id)
        
        # Optimization: Check if vectors already exist (Auto-Resume)
        if chroma_client.is_collection_populated(session_id):
            logger.info(f"Session {session_id} has existing vectors. Skipping ingestion.")
            session_manager.update_session(session_id, status="completed", files_processed=0, chunks_created=0)
            return IngestResponse(
                session_id=session_id,
                status="completed",
                files_processed=0,
                chunks_created=0,
                manifest={},
                vector_status="already_loaded"
            )

        session_manager.update_session(session_id, status="cloning")
        logger.info(f"Starting ingestion pipeline for: {session_id}")

        # Step 2: Clone repository (Blocking IO in Thread)
        repo_path = None
        try:
            repo_info = await asyncio.to_thread(load_github_repo, repo_url, session_id)
            repo_path = repo_info["repo_path"]
            session_manager.update_session(session_id, status="filtering", repo_path=repo_path)
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            raise HTTPException(status_code=500, detail=f"Failed to clone: {str(e)}")

        # Step 3: Filter
        try:
            repo_path_obj = Path(repo_path)
            filtered_files = filter_repository_files(repo_path_obj)
            if not filtered_files:
                 raise Exception("No processable files found")
            session_manager.update_session(session_id, status="processing", files_count=len(filtered_files))
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            raise HTTPException(status_code=500, detail=f"Failed to filter: {str(e)}")

        # Step 4: Manifest
        manifest = {}
        try:
            manifest = generate_repo_manifest(repo_path, [str(f.relative_to(repo_path_obj)) for f in filtered_files])
            session_manager.store_manifest(session_id, manifest)
            session_manager.update_session(session_id, status="chunking")
        except Exception as e:
             logger.error(f"Manifest generation failed: {e}")

        # Step 5: Chunk
        all_chunks = []
        files_processed = 0
        try:
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
            session_manager.store_chunks(session_id, all_chunks)
        except Exception as e:
            session_manager.update_session(session_id, status="failed")
            raise HTTPException(status_code=500, detail=f"Chunking failed: {str(e)}")

        # Step 6: Vector Store
        vector_status = "failed"
        if all_chunks:
            try:
                chroma_client.create_session_collection(session_id)
                chroma_client.add_chunks(session_id, all_chunks)
                vector_status = "stored"
            except Exception as e:
                logger.error(f"Vector store failed: {e}")
        
        # Step 7: Mind Map Generation (For All Modes)
        # We now support architect, extension, system_design
        if mode in ["architect", "extension", "system_design", "debugger"]:
             try:
                 # Construct context for Mind Map (Manifest + Entry Points)
                 # We reuse the manifest generated earlier
                 manifest_str = str(manifest)
                 # Limit size just in case
                 context_for_mm = f"Repo URL: {repo_url}\nManifest: {manifest_str[:15000]}"
                 
                 from app.api.chat import get_gemini_client
                 from app.api.chat import get_gemini_client
                 gemini = get_gemini_client()
                 # Pass the mode to select the correct prompting strategy
                 mm_result = gemini.generate_mind_map(context_for_mm, mode=mode)
                 
                 mm_json_str = mm_result.get("content", "[]")
                 mm_usage = mm_result.get("usage", {})

                 # Clean JSON (remove markdown fences if present)
                 import json
                 clean_json = mm_json_str.replace("```json", "").replace("```", "").strip()
                 mind_map_data = json.loads(clean_json)
                 
                 # Store in Mongo - Update Usage First
                 from app.db.mongo import get_mongo_client
                 mongo_client = get_mongo_client()
                 
                 # --- USAGE TRACKING (Mind Map) ---
                 if mm_usage and mongo_client:
                     from app.utils.pricing import calculate_gemini_cost
                     price_mm = calculate_gemini_cost("gemini-2.0-flash", mm_usage['prompt_tokens'], mm_usage['completion_tokens'])
                     await mongo_client.update_user_usage(user_id, mm_usage['total_tokens'], price_mm)
                     logger.info(f"Mind Map tracked: {mm_usage['total_tokens']} tokens, ${price_mm:.6f}")
                 
                 # Wait! Generate Phase 1 Content immediately.
                 if mind_map_data and len(mind_map_data) > 0:
                     first_step = mind_map_data[0]
                     try:
                         # Use Vectors for better context if possible, or fallback to manifest
                         context_text_phase1 = context_for_mm # Default
                         
                         if vector_status == "stored":
                             try:
                                 query = f"{first_step['title']} {first_step['description']}"
                                 # We just stored chunks, so we can query them.
                                 # Ensure collection is ready? usually immediate.
                                 context_chunks = chroma_client.query(session_id, query, top_k=5)
                                 if context_chunks:
                                     # Results are usually list of dicts or list of strings depending on client
                                     # Let's extract safely
                                     context_str_list = [c.get("content", "") for c in context_chunks if isinstance(c, dict)]
                                     if not context_str_list and isinstance(context_chunks, list):
                                         context_str_list = [str(c) for c in context_chunks if isinstance(c, str)]
                                     context_text_phase1 = "\n".join(context_str_list)
                             except Exception as vector_e:
                                 logger.warning(f"Vector query for Phase 1 failed: {vector_e}")
                         
                         # Generate Detailed Content
                         phase1_result = gemini.generate_phase_content(context_text_phase1, first_step['title'], first_step['description'])
                         phase1_content = phase1_result.get("content", "Failed")
                         phase1_usage = phase1_result.get("usage", {})
                         
                         mind_map_data[0]["content"] = phase1_content
                         
                         # --- USAGE TRACKING (Phase 1) ---
                         if phase1_usage and mongo_client:
                             from app.utils.pricing import calculate_gemini_cost
                             price_p1 = calculate_gemini_cost("gemini-2.0-flash", phase1_usage['prompt_tokens'], phase1_usage['completion_tokens'])
                             await mongo_client.update_user_usage(user_id, phase1_usage['total_tokens'], price_p1)
                             logger.info(f"Phase 1 tracked: {phase1_usage['total_tokens']} tokens, ${price_p1:.6f}")
                             
                         logger.info("Phase 1 content generated successfully during ingestion.")
                         
                     except Exception as p1_e:
                         logger.error(f"Phase 1 generation failed: {p1_e}")
                 
                 # Store in Mongo
                 if mongo_client:
                     await mongo_client.update_chat_mind_map(session_id, mind_map_data)
                     
             except Exception as e:
                 logger.error(f"Mind Map generation failed: {e}")
                 # Non-critical, continue

        session_manager.update_session(
            session_id, 
            status="completed", 
            files_processed=files_processed, 
            chunks_created=len(all_chunks)
        )
        
        # Cleanup
        if background_tasks:
            background_tasks.add_task(cleanup_repo_directory, session_id)
        else:
            # If no background tasks context (e.g. called from another function), we might want to clean up immediately or spawn a task
            # For robustness, we'll just run it immediately or launch a task
            asyncio.create_task(asyncio.to_thread(cleanup_repo_directory, session_id))

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
        logger.error(f"Pipeline failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Pipeline failed: {str(e)}")

@router.post("", response_model=IngestResponse)
async def ingest_repository(request: IngestRequest, background_tasks: BackgroundTasks, user: TokenData = Depends(get_current_user)):
    """
    Synchronous repository ingestion (Async Handler).
    """
    try:
        # Validate repo URL
        if not request.repo_url or not request.repo_url.strip():
            raise HTTPException(status_code=400, detail="Repository URL is required")
        
        # Create session ID
        session_id = session_manager.create_session(repo_url=request.repo_url)
        
        # Create Chat Record in Mongo
        from app.db.mongo import get_mongo_client
        mongo_client = get_mongo_client()
        if mongo_client and mongo_client.is_connected():
             chat_data = {
                "chat_id": session_id,
                "user_id": request.user_id, # Or user.user_id
                "repo_url": request.repo_url,
                "repo_name": request.repo_url.split("/")[-1],
                "mode": request.mode,
                "created_at": datetime.utcnow()
            }
             await mongo_client.create_chat(chat_data)

        # Run Pipeline
        return await run_ingestion_pipeline(session_id, request.repo_url, request.user_id, request.mode, background_tasks)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingest failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        

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

        # Check if vector data is already valid (populated)
        if chroma_client.is_collection_populated(session_id):
             logger.info(f"Session {session_id} already has vector data. Skipping re-ingestion.")
             session_manager.update_session(session_id, status="completed")
             return IngestResponse(
                session_id=session_id,
                status="completed",
                files_processed=0,
                chunks_created=0,
                manifest={}, 
                vector_status="already_loaded"
            )
        
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
