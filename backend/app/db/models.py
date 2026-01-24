"""Pydantic models for database entities."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class User(BaseModel):
    """User model."""
    user_id: str
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    total_tokens: int = 0
    total_due_price: float = 0.0
    total_paid_price: float = 0.0


class Chat(BaseModel):
    """Chat session model."""
    chat_id: str
    user_id: str
    repo_url: str
    repo_name: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

class Prompt(BaseModel):
    """Prompt record model (formerly UsageRecord)."""
    prompt_id: str
    chat_id: str  # Links to Chat.chat_id
    user_id: str
    action: str = Field(..., description="Action type: 'chat', 'ingest', etc.")
    question: Optional[str] = None
    answer: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    model: str = "gemini-2.0-flash"
    price: float = 0.0
    timestamp: datetime
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")
