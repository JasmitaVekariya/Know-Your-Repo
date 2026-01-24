"""User management API endpoints."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid
from app.db.mongo import get_mongo_client

router = APIRouter()

class UserRegisterRequest(BaseModel):
    """Request model for user registration."""
    email: str
    name: Optional[str] = None

from typing import Optional, Union, Any

class UserResponse(BaseModel):
    """Response model for user data."""
    user_id: str
    email: str
    name: Optional[str] = None
    created_at: Union[datetime, str]
    
    class Config:
        extra = "ignore" 
        # Pydantic v2: model_config = ConfigDict(extra='ignore')

@router.post("/register", response_model=UserResponse)
async def register_user(request: UserRegisterRequest):
    """
    Register a new user to MongoDB Atlas.
    
    Args:
        request: UserRegisterRequest containing user details
        
    Returns:
        UserResponse with user data
    """
    client_wrapper = get_mongo_client()
    if not client_wrapper or not client_wrapper.is_connected():
        raise HTTPException(status_code=503, detail="Database connection unavailable")
        
    db = client_wrapper.db
    users_collection = db.users
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": request.email})
    if existing_user:
        # Return existing user if email matches
        # Convert _id to string if needed, but we use user_id field
        return UserResponse(**existing_user)
    
    user_id = str(uuid.uuid4())
    user_data = {
        "user_id": user_id,
        "email": request.email,
        "name": request.name,
        "created_at": datetime.now().isoformat()
    }
    
    await users_collection.insert_one(user_data)
    
    return UserResponse(**user_data)

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user by ID from MongoDB.
    
    Args:
        user_id: User identifier
        
    Returns:
        UserResponse with user data
    """
    client_wrapper = get_mongo_client()
    if not client_wrapper or not client_wrapper.is_connected():
        raise HTTPException(status_code=503, detail="Database connection unavailable")
        
    db = client_wrapper.db
    users_collection = db.users
    
    user = await users_collection.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Validation/Cleanup for legacy users
    if not user.get("name"):
        user["name"] = user["email"].split("@")[0]
    
    return UserResponse(**user)

class DashboardResponse(BaseModel):
    """Response model for user dashboard."""
    user_id: str
    name: Optional[str] = None
    total_prompts: int
    total_tokens: int
    total_due_price: float
    total_paid_price: float
    price_left_to_pay: float
    usage_chart: list  # List of {date, tokens, cost}

from app.core.auth import get_current_user, TokenData
from fastapi import Depends

@router.get("/{user_id}/dashboard", response_model=DashboardResponse)
async def get_user_dashboard(user_id: str, days: int = 30, current_user: TokenData = Depends(get_current_user)):
    """
    Get comprehensive dashboard statistics for a user.
    """
    client_wrapper = get_mongo_client()
    if not client_wrapper or not client_wrapper.is_connected():
        raise HTTPException(status_code=503, detail="Database connection unavailable")
        
    # Check if user exists
    user = await client_wrapper.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Get stats
    prompt_count = await client_wrapper.get_prompt_count(user_id)
    chart_data = await client_wrapper.get_usage_chart(user_id, days)
    
    # SELF-HEALING: If totals are 0 but usage > 0, recalculate
    if user.get("total_tokens", 0) == 0 and prompt_count > 0:
        await client_wrapper.recalculate_user_totals(user_id)
        # Fetch updated user
        user = await client_wrapper.get_user(user_id)
        
    total_due = user.get("total_due_price", 0.0)
    total_paid = user.get("total_paid_price", 0.0)
    
    # Format chart data
    formatted_chart = []
    for item in chart_data:
        formatted_chart.append({
            "date": item["_id"],
            "tokens": item["tokens"],
            "cost": round(item["cost"], 6)
        })
    
    return DashboardResponse(
        user_id=user["user_id"],
        name=user.get("name") or user.get("email", "").split("@")[0],
        total_prompts=prompt_count,
        total_tokens=user.get("total_tokens", 0),
        total_due_price=round(total_due, 4),
        total_paid_price=round(total_paid, 4),
        price_left_to_pay=round(total_due - total_paid, 4),
        usage_chart=formatted_chart
    )

@router.get("/{user_id}/chats")
async def get_user_chat_history(user_id: str):
    """
    Get list of past chat sessions.
    """
    client_wrapper = get_mongo_client()
    if not client_wrapper or not client_wrapper.is_connected():
        raise HTTPException(status_code=503, detail="Database connection unavailable")
        
    chats = await client_wrapper.get_user_chats(user_id)
    
    # Format for frontend
    formatted_chats = []
    for chat in chats:
        formatted_chats.append({
            "session_id": chat["chat_id"],
            "repo_url": chat["repo_url"],
            "repo_name": chat.get("repo_name", "Unknown Repo"),
            "mode": chat.get("mode", "architect"),
            "created_at": chat["created_at"],
            "is_favorite": chat.get("is_favorite", False)
        })
        
    return formatted_chats
