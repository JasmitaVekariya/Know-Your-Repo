"""Chat API endpoints for Q&A with repository context."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.core.session import session_manager
from app.core.config import config
from app.vector.chroma import ChromaClient
from app.llm.gemini import GeminiClient
from app.llm.prompts import CHAT_PROMPT_TEMPLATE

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

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, user: TokenData = Depends(get_current_user)):
    """
    Process a chat message and retrieve relevant context.
    
    Args:
        request: ChatRequest containing session_id and message
        
    Returns:
        ChatResponse with answer
    """
    # Verify session exists
    session = session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Query ChromaDB (RAG)
    try:
        results = chroma_client.query(request.session_id, request.message, top_k=10)
    except Exception as e:
        # If retrieval fails, we might still want to answer if it's a general question?
        # But for this specific agent, context is key.
        # Log and proceed with empty context?
        logger.warning(f"Retrieval failed for session {request.session_id}: {e}")
        results = []
    
    # Format chunks for context
    context_text = ""
    
    for r in results:
        chunk_content = r.get("content", "")
        metadata = r.get("metadata", {})
        file_path = metadata.get("file_path", "unknown")
        
        chunk_display = f"File: {file_path}\nCode:\n{chunk_content}\n---\n"
        context_text += chunk_display
    
    # Construct prompt
    prompt = CHAT_PROMPT_TEMPLATE.format(
        context=context_text,
        question=request.message
    )
    
    # Generate Answer
    gemini = get_gemini_client()
    try:
        answer = gemini.generate_response(prompt)
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
        prompt_tokens = count_tokens(prompt)
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
