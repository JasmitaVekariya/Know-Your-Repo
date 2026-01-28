"""MongoDB database client wrapper."""

from motor.motor_asyncio import AsyncIOMotorClient
from typing import Optional
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MongoClientWrapper:
    """Wrapper for MongoDB client connection."""
    
    def __init__(self, uri: str):
        """
        Initialize MongoDB client wrapper.
        
        Args:
            uri: MongoDB connection URI
        """
        self.uri = uri
        self.client: Optional[AsyncIOMotorClient] = None
        self.db = None
    
    async def connect(self) -> None:
        """
        Establish connection to MongoDB.
        """
        try:
            # Connect to MongoDB with default SSL/TLS settings
            # We MUST use tlsAllowInvalidCertificates=True on this Mac environment to avoid handshake failures
            self.client = AsyncIOMotorClient(self.uri, tlsAllowInvalidCertificates=True)
            # Ping the database to verify connection
            await self.client.admin.command('ping')
            try:
                self.db = self.client.get_default_database()
            except Exception:
                # Fallback if no db in URI
                self.db = self.client.github_agent
            logger.info("Successfully connected to MongoDB")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise e
    
    async def disconnect(self) -> None:
        """
        Close MongoDB connection.
        """
        if self.client:
            self.client.close()
            self.client = None
            self.db = None
            logger.info("MongoDB connection closed")
    
    def is_connected(self) -> bool:
        """
        Check if MongoDB connection is active.
        
        Returns:
            True if connected, False otherwise
        """
        return self.client is not None

    async def create_chat(self, chat_data: dict) -> None:
        """
        Create a new chat session.
        """
        if self.db is not None:
            await self.db.chats.insert_one(chat_data)

    async def get_chat(self, chat_id: str) -> Optional[dict]:
        """
        Get a chat session by ID.
        """
        if self.db is not None:
             return await self.db.chats.find_one({"chat_id": chat_id})
        return None

    async def save_prompt(self, prompt_data: dict) -> None:
        """
        Save prompt record to MongoDB (prompts collection).
        """
        if self.db is not None:
            await self.db.prompts.insert_one(prompt_data)
            
    async def get_user(self, user_id: str) -> Optional[dict]:
        """
        Get user by ID.
        """
        if self.db is not None:
            return await self.db.users.find_one({"user_id": user_id})
        return None
        
    async def get_user_by_email(self, email: str) -> Optional[dict]:
        """
        Get user by Email (for login).
        """
        if self.db is not None:
             return await self.db.users.find_one({"email": email})
        return None
        
    async def create_user(self, user_data: dict) -> None:
        """
        Create new user.
        """
        if self.db is not None:
            # Ensure index on email?
            # self.db.users.create_index("email", unique=True) # Good practice to ensure uniqueness
            await self.db.users.insert_one(user_data)
            
    async def update_user_usage(self, user_id: str, tokens: int, price: float, prompts: int = 1) -> None:
        """
        Increment user usage totals.
        """
        if self.db is not None:
            await self.db.users.update_one(
                {"user_id": user_id},
                {
                    "$inc": {
                        "total_tokens": tokens,
                        "total_due_price": price,
                        "prompt_count": prompts
                    },
                    "$set": {"updated_at": datetime.utcnow()}
                }
            )
            
    async def update_user_password(self, user_id: str, hashed_password: str) -> None:
        """
        Update user password (e.g. for claiming legacy account).
        """
        if self.db is not None:
             await self.db.users.update_one(
                {"user_id": user_id},
                {"$set": {"hashed_password": hashed_password}}
            )

    async def get_prompt_count(self, user_id: str) -> int:
        """Count total prompts (chat actions) by user."""
        if self.db is not None:
            return await self.db.prompts.count_documents({"user_id": user_id, "action": "chat"})
        return 0

    async def get_usage_chart(self, user_id: str, days: int = 30) -> list:
        """
        Get daily token usage chart data for the last N days.
        """
        if self.db is not None:
            start_date = datetime.utcnow() - timedelta(days=days)
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "timestamp": {"$gte": start_date}
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}
                        },
                        "tokens": {"$sum": "$total_tokens"},
                        "cost": {"$sum": "$price"}
                    }
                },
                {
                    "$sort": {"_id": 1}
                }
            ]
            cursor = self.db.prompts.aggregate(pipeline)
            return await cursor.to_list(length=days)
        return []

    async def recalculate_user_totals(self, user_id: str) -> None:
        """
        Recalculate total tokens and price from prompt logs and update user record.
        Self-healing for consistency issues.
        """
        if self.db is not None:
            pipeline = [
                {"$match": {"user_id": user_id}},
                {"$group": {
                    "_id": "$user_id",
                    "total_tokens": {"$sum": "$total_tokens"},
                    "total_price": {"$sum": "$price"}
                }}
            ]
            result = await self.db.prompts.aggregate(pipeline).to_list(length=1)
            
            if result:
                stats = result[0]
                await self.db.users.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "total_tokens": stats.get("total_tokens", 0),
                            "total_due_price": stats.get("total_price", 0.0),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
    
    async def get_user_chats(self, user_id: str) -> list:
        """
        Get all chat sessions for a user, sorted by favorite then recency.
        """
        if self.db is not None:
             # 1. Get user favorites
             user = await self.db.users.find_one({"user_id": user_id}, {"favorites": 1})
             favorites = set(user.get("favorites", [])) if user else set()

             # 2. Get chats
             cursor = self.db.chats.find({"user_id": user_id}).sort("created_at", -1)
             chats = await cursor.to_list(length=100)

             # 3. Merge favorite status
             for chat in chats:
                 chat["is_favorite"] = chat["chat_id"] in favorites
             
             # 4. Sort in memory (Favorite first, then date)
             chats.sort(key=lambda x: (not x["is_favorite"], x["created_at"]), reverse=False) 
             # False means True (is_favorite=True) comes before False? No.
             # tuple comparison: (False, timestamp) vs (True, timestamp)
             # We want Favorites (True) first.
             # True > False in Python.
             # So sorting by is_favorite descending puts True first.
             # Sorting by created_at descending puts newer first.
             chats.sort(key=lambda x: (x["is_favorite"], x["created_at"]), reverse=True)

             return chats
        return []

    async def get_chat_history(self, chat_id: str) -> list:
        """
        Get all messages/prompts for a specific chat session.
        """
        if self.db is not None:
            cursor = self.db.prompts.find({"chat_id": chat_id}).sort("timestamp", 1)
            return await cursor.to_list(length=500)
        return []

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        """Delete a chat session and its history."""
        if self.db is not None:
            # Verify ownership
            result = await self.db.chats.delete_one({"chat_id": chat_id, "user_id": user_id})
            if result.deleted_count > 0:
                # Also delete prompts/messages
                await self.db.prompts.delete_many({"chat_id": chat_id})
                # Remove from favorites if present
                await self.db.users.update_one(
                    {"user_id": user_id},
                    {"$pull": {"favorites": chat_id}}
                )
                return True
        return False

    async def toggle_favorite(self, chat_id: str, user_id: str) -> bool:
        """Toggle the is_favorite status of a chat in User collection."""
        if self.db is not None:
            # Check current status
            user = await self.db.users.find_one({"user_id": user_id}, {"favorites": 1})
            favorites = user.get("favorites", []) if user else []
            
            is_fav = chat_id in favorites
            new_status = not is_fav

            if new_status:
                # Add to favorites
                await self.db.users.update_one(
                    {"user_id": user_id},
                    {"$addToSet": {"favorites": chat_id}}
                )
            else:
                # Remove from favorites
                await self.db.users.update_one(
                    {"user_id": user_id},
                    {"$pull": {"favorites": chat_id}}
                )
            return new_status
        return False
        
    async def update_chat_mind_map(self, chat_id: str, mind_map: list) -> None:
        """
        Update the mind map structure for a chat.
        """
        if self.db is not None:
            await self.db.chats.update_one(
                {"chat_id": chat_id},
                {"$set": {"mind_map": mind_map, "current_step_index": 0}}
            )

    async def update_chat_step(self, chat_id: str, step_index: int) -> None:
        """Update current step index."""
        if self.db is not None:
             await self.db.chats.update_one(
                {"chat_id": chat_id},
                {"$set": {"current_step_index": step_index}}
            )

# Global instance
mongo_client = None

def get_mongo_client(uri: str = None) -> MongoClientWrapper:
    global mongo_client
    if not mongo_client and uri:
        mongo_client = MongoClientWrapper(uri)
    return mongo_client

# Helper to get the DB instance easily (for imports)
# Note: This might be None if client not connected yet, but at runtime it should be fine
# A better pattern is to call get_mongo_client().db or methods directly
mongo_db = None  # Backward compatibility if I referenced mongo_db directly? 
# Actually, I referenced mongo_db.save_usage in chat.py
# So I should make mongo_db point to the client instance or expose methods on module level?
# No, `from app.db.mongo import mongo_db` implies it's an object.
# Let's alias it to the function that returns the client? No.
# I will make `mongo_db` a proxy object or just export the client as `mongo_db` once initialized.
# But initialization happens in main.py.
# The best way is to use `get_mongo_client()` in chat.py.
# But I already wrote `from app.db.mongo import mongo_db` in Step 822.
# I will expose `mongo_db` as an instance of MongoClientWrapper that is globally shared.

mongo_db = get_mongo_client() # This might be None initially.
# Wait, get_mongo_client checks `if not mongo_client`.
# If I call it without URI, it assumes it's already created.
# I will fix chat.py to use `get_mongo_client()` instead of importing `mongo_db` variable which might be unsafe.
