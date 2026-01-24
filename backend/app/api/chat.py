"""Chat API endpoints for Q&A with repository context."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.core.session import session_manager
from app.core.config import config
from app.vector.chroma import ChromaClient
from app.llm.gemini import GeminiClient
from app.llm.prompts import (
    SYSTEM_PROMPTS, 
    CHAT_PROMPT_TEMPLATE, 
    SUMMARY_PROMPT_TEMPLATE,
    COMMON_INSTRUCTIONS
)

logger = logging.getLogger(__name__)

router = APIRouter()
chroma_client = ChromaClient()

# Initialize Gemini Client (lazy load or global?)
# Better to initialize per request or catch config errors early
# For now, we instantiate when needed to ensure config IS loaded
def get_gemini_client() -> GeminiClient:
    try:
        return GeminiClient(api_key=config.GEMINI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Gemini client: {e}")
        raise HTTPException(status_code=500, detail="LLM service unavailable")

class ChatRequest(BaseModel):
    """Request model for chat messages."""
    session_id: str
    user_id: str
    message: str

class RetrievedChunk(BaseModel):
    """Model for retrieved text chunk."""
    content: str
    metadata: Dict[str, Any]

class ChatResponse(BaseModel):
    """Response model for chat replies."""
    answer: str

from app.core.auth import get_current_user, TokenData
from fastapi import Depends

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, background_tasks: BackgroundTasks, user: TokenData = Depends(get_current_user)):
    """
    Process a chat message and retrieve relevant context.
    
    Args:
        request: ChatRequest containing session_id and message
        
    Returns:
        ChatResponse with answer
    """
    # Verify session exists
    session = session_manager.get_session(request.session_id)
    
    # Attempt resurrection if missing from memory
    if not session:
        if chroma_client.is_collection_populated(request.session_id):
            logger.info(f"Resurrecting session {request.session_id} from persistent storage")
            session_manager.resurrect_session(request.session_id)
            session = session_manager.get_session(request.session_id)
        else:
            # Auto-Recovery: content missing from Chroma (e.g. server restart/cleanup)
            logger.info(f"Session {request.session_id} not found in memory or vector store. Checking database...")
            
            from app.db.mongo import get_mongo_client
            mongo_client = get_mongo_client()
            chat_record = await mongo_client.get_chat(request.session_id)
            
            if chat_record and chat_record.get("repo_url"):
                logger.info(f"Found chat record for {request.session_id}. Triggering auto-reingestion.")
                from app.api.ingest import run_ingestion_pipeline
                
                # Run ingestion synchronously (await) so we can answer the user
                # This might take time, but it's better than failing.
                await run_ingestion_pipeline(
                    session_id=request.session_id,
                    repo_url=chat_record["repo_url"],
                    user_id=chat_record.get("user_id", user.user_id),
                    background_tasks=background_tasks
                )
                
                # Fetch session again
                session = session_manager.get_session(request.session_id)
            
            if not session:
                raise HTTPException(status_code=404, detail="Session not found or expired")
    
    # Heartbeat: Update last accessed time
    session_manager.touch_session(request.session_id)
    
    # --- RAG ENHANCEMENT ---
    
    # 1. Fetch the high-level manifest
    manifest = session_manager.get_manifest(request.session_id)
    manifest_text = ""
    if manifest:
        # Safely get fields with defaults
        arch = manifest.get('architecture_summary', 'Not available')
        stack = ', '.join(manifest.get('tech_stack', []))
        entry = ', '.join(manifest.get('entry_points', []))
        
        manifest_text = f"Architecture Summary: {arch}\n"
        manifest_text += f"Tech Stack: {stack}\n"
        manifest_text += f"Entry Points: {entry}\n"

    # 2. Adjust Top-K based on query intent
    # Check for summary-type keywords
    summary_keywords = ["summary", "overview", "architecture", "explain project", "what does this do", "explain this repo"]
    is_summary_query = any(word in request.message.lower() for word in summary_keywords)
    
    # Increase context for summaries to capture more breadth
    top_k = 12 if is_summary_query else 5
    
    # Query ChromaDB (RAG)
    try:
        results = chroma_client.query(request.session_id, request.message, top_k=top_k)
    except Exception as e:
        logger.warning(f"Retrieval failed for session {request.session_id}: {e}")
        results = []
    
    # 3. Build the final prompt with Manifest + Chunks
    context_text = ""
    
    if manifest_text:
        context_text += f"### REPOSITORY MANIFEST (High Level)\n{manifest_text}\n\n"
        
    context_text += "### RELEVANT CODE CHUNKS\n"
    
    for r in results:
        chunk_content = r.get("content", "")
        metadata = r.get("metadata", {})
        file_path = metadata.get("file_path", "unknown")
        
        chunk_display = f"File: {file_path}\nCode:\n{chunk_content}\n---\n"
        context_text += chunk_display
    
    # Construct prompt
    # Select template based on intent
    if is_summary_query:
        # Use the specific Summary Blueprint template
        user_prompt = SUMMARY_PROMPT_TEMPLATE.format(context=context_text)
        # Summary always uses the Architect persona
        system_prompt_to_use = SYSTEM_PROMPTS["architect"]
    else:
        # Use standard Chat template
        user_prompt = CHAT_PROMPT_TEMPLATE.format(context=context_text, question=request.message)
        
        # Determine strict mode from chat metadata
        chat_mode = "architect" # default
        try:
             # Fetch mode from MongoDB chat record
             from app.db.mongo import get_mongo_client
             mongo_client = get_mongo_client()
             if mongo_client:
                 chat_record = await mongo_client.get_chat(request.session_id)
                 if chat_record:
                     chat_mode = chat_record.get("mode", "architect")
        except Exception as e:
            logger.warning(f"Failed to fetch chat mode: {e}")
            
        system_prompt_to_use = SYSTEM_PROMPTS.get(chat_mode, SYSTEM_PROMPTS["architect"])
        
    # Combine System Persona + Common Rules + Specific Template
    final_prompt = f"{system_prompt_to_use}\n\n{COMMON_INSTRUCTIONS}\n\n{user_prompt}"
    
    # Generate Answer
    gemini = get_gemini_client()
    try:
        answer = gemini.generate_response(final_prompt)
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate answer: {str(e)}")
    
    # --- Token & Cost Tracking ---
    try:
        from app.utils.token_counter import count_tokens
        from app.utils.pricing import calculate_gemini_cost
        from datetime import datetime
        import uuid
        
        # 1. Count Tokens
        prompt_tokens = count_tokens(final_prompt)
        completion_tokens = count_tokens(answer)
        total_tokens = prompt_tokens + completion_tokens
        
        # 2. Calculate Price
        model_name = "gemini-2.0-flash"
        price = calculate_gemini_cost(model_name, prompt_tokens, completion_tokens)
        
        # 3. Get User ID
        user_id = request.user_id 
        
        # 4. Create Prompt Record
        prompt_id = str(uuid.uuid4())
        prompt_data = {
            "prompt_id": prompt_id,
            "chat_id": request.session_id, # Links to Chat
            "user_id": user_id,
            "action": "chat",
            "question": request.message,
            "answer": answer,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": total_tokens,
            "model": model_name,
            "price": price,
            "timestamp": datetime.utcnow()
        }
        
        # 5. Async Database Update
        from app.db.mongo import get_mongo_client
        mongo_client = get_mongo_client()
        
        # Save Record
        await mongo_client.save_prompt(prompt_data)
        
        # Update User Totals
        user = await mongo_client.get_user(user_id)
        if not user:
            await mongo_client.create_user({
                "user_id": user_id,
                "email": "demo@example.com",
                "created_at": datetime.utcnow()
            })
            
        await mongo_client.update_user_usage(user_id, total_tokens, price)
        
        logger.info(f"Chat tracked: {total_tokens} tokens, ${price:.6f}")
        
    except Exception as e:
        # Don't fail the request if tracking fails
        logger.error(f"Failed to track usage: {e}")

    return ChatResponse(
        answer=answer
    )

@router.get("/{session_id}/history")
async def get_chat_history(session_id: str):
    """
    Get chat history for a session.
    """
    from app.db.mongo import get_mongo_client
    mongo_client = get_mongo_client()
    
    if not mongo_client or not mongo_client.is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")
        
    history = await mongo_client.get_chat_history(session_id)
    
    messages = []
    for item in history:
        # Each prompt record has a question (user) and answer (bot)
        if item.get("question"):
            messages.append({"role": "user", "content": item["question"]})
        if item.get("answer"):
             messages.append({"role": "bot", "content": item["answer"]})
             
    return messages

@router.get("/{session_id}/metadata")
async def get_chat_metadata(session_id: str):
    """
    Get chat session metadata (mode, mind_map, current_step).
    """
    from app.db.mongo import get_mongo_client
    mongo_client = get_mongo_client()
    if not mongo_client:
         raise HTTPException(status_code=503, detail="Database unavailable")
         
    chat = await mongo_client.get_chat(session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    return {
        "mode": chat.get("mode", "architect"),
        "mind_map": chat.get("mind_map", []),
        "current_step_index": chat.get("current_step_index", 0),
        "repo_name": chat.get("repo_name", "")
    }

@router.delete("/{session_id}")
async def delete_chat(session_id: str, user: TokenData = Depends(get_current_user)):
    """
    Delete a chat session.
    """
    from app.db.mongo import get_mongo_client
    mongo_client = get_mongo_client()
    
    if not mongo_client or not mongo_client.is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")
        
    # Delete from Mongo
    deleted = await mongo_client.delete_chat(session_id, user.user_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat not found or access denied")
        
    # Delete from Chroma
    try:
        chroma_client.cleanup_session(session_id)
    except Exception as e:
        logger.warning(f"Failed to cleanup Chroma for session {session_id}: {e}")
        
    # Delete from memory
    session_manager.delete_session(session_id)
    
    return {"status": "deleted"}

@router.post("/{session_id}/step")
async def update_chat_step(session_id: str, request: Dict[str, int]):
    """
    Update the current step index in the mind map.
    """
    step_index = request.get("step_index", 0)
    
    from app.db.mongo import get_mongo_client
    mongo_client = get_mongo_client()
    
    if not mongo_client or not mongo_client.is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")
        
    await mongo_client.update_chat_step(session_id, step_index)
    return {"status": "updated", "current_step_index": step_index}

@router.post("/{session_id}/favorite")
async def toggle_favorite(session_id: str, user: TokenData = Depends(get_current_user)):
    """
    Toggle favorite status of a chat.
    """
    from app.db.mongo import get_mongo_client
    mongo_client = get_mongo_client()
    
    if not mongo_client or not mongo_client.is_connected():
        raise HTTPException(status_code=503, detail="Database unavailable")
        
    new_status = await mongo_client.toggle_favorite(session_id, user.user_id)
    return {"session_id": session_id, "is_favorite": new_status}

@router.post("/{session_id}/phase/generate")
async def generate_phase(session_id: str, request: Dict[str, int]):
    """
    Generate detailed content for a specific phase (lazy load).
    """
    step_index = request.get("step_index", 0)
    
    from app.db.mongo import get_mongo_client
    mongo_client = get_mongo_client()
    if not mongo_client:
         raise HTTPException(status_code=503, detail="Database unavailable")
         
    chat = await mongo_client.get_chat(session_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
        
    mind_map = chat.get("mind_map", [])
    if step_index < 0 or step_index >= len(mind_map):
        raise HTTPException(status_code=400, detail="Invalid step index")
        
    step = mind_map[step_index]
    
    # If content already exists and is significant, return it (cache)
    if step.get("content") and len(step["content"]) > 50:
        return {"step_index": step_index, "content": step["content"], "status": "cached"}
        
    # Generate
    try:
        # Use RAG Context
        from app.vector.chroma import ChromaClient
        chroma = ChromaClient()
        query = f"{step['title']} {step['description']}"
        context_chunks = chroma.query(session_id, query, top_k=5)
        
        # Extract content from chunks (chunks are dicts)
        context_str_list = [c.get("content", "") for c in context_chunks if isinstance(c, dict)]
        if not context_str_list and isinstance(context_chunks, list):
             context_str_list = [str(c) for c in context_chunks if isinstance(c, str)]
             
        context_text = "\\n".join(context_str_list)
        
        gemini = get_gemini_client()
        content = gemini.generate_phase_content(context_text, step["title"], step["description"])
        
        # Update DB
        mind_map[step_index]["content"] = content
        await mongo_client.update_chat_mind_map(session_id, mind_map)
        
        return {"step_index": step_index, "content": content, "status": "generated"}
        
    except Exception as e:
        logger.error(f"Phase generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
