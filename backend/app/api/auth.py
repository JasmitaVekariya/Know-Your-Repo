from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from app.db.mongo import get_mongo_client
from app.core.auth import get_password_hash, verify_password, create_access_token, Token, TokenData, get_current_user
from pydantic import BaseModel
import uuid
from datetime import datetime, timedelta

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str
    name: str = None  # Add name field

@router.post("/register", response_model=Token)
async def register(user: UserCreate):
    try:
        client = get_mongo_client()
        if not client or not client.is_connected():
             raise HTTPException(status_code=503, detail="Database unavailable")
             
        # Check existing
        existing = await client.get_user_by_email(user.email)
        
        user_id = None
        hashed_password = get_password_hash(user.password)
        
        if existing:
            if not existing.get("hashed_password"):
                # Legacy user claiming account
                user_id = existing["user_id"]
                await client.update_user_password(user_id, hashed_password)
                # Should we update name too if missing?
            else:
                raise HTTPException(status_code=400, detail="Email already registered")
        else:
            # Create user
            user_id = str(uuid.uuid4())
            user_data = {
                "user_id": user_id,
                "email": user.email,
                "name": user.name or user.email.split('@')[0], # Fallback to email prefix
                "hashed_password": hashed_password,
                "created_at": datetime.utcnow(),
                "total_tokens": 0,
                "total_due_price": 0.0
            }
            await client.create_user(user_data)
        
        # Return login token immediately
        access_token_expires = timedelta(minutes=60 * 24)
        access_token = create_access_token(
            data={"sub": user_id, "email": user.email}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration Error: {str(e)}") # Print to console for now
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    client = get_mongo_client()
    user = await client.get_user_by_email(form_data.username)
    
    if not user or not verify_password(form_data.password, user.get("hashed_password")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token_expires = timedelta(minutes=60 * 24)
    access_token = create_access_token(
        data={"sub": user["user_id"], "email": user["email"]}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
    
@router.get("/me", response_model=TokenData)
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    return current_user
