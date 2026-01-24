"""FastAPI application entry point."""

import logging
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import ingest, chat, user

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from contextlib import asynccontextmanager
from app.core.cleanup import start_cleanup_loop

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize MongoDB and start cleanup loop
    from app.core.config import config
    from app.db.mongo import get_mongo_client
    
    # Initialize MongoDB connection
    mongo_client = get_mongo_client(config.MONGO_URI)
    await mongo_client.connect()
    
    cleanup_task = asyncio.create_task(start_cleanup_loop())
    
    yield
    
    # Shutdown: Close MongoDB connection and cancel cleanup loop
    await mongo_client.disconnect()
    
    # Clean up ChromaDB storage (Ephemeral means ephemeral!)
    import shutil
    import os
    if os.path.exists("./chroma_store"):
        # Ensure client is closed/released if possible via GC or similar
        # But removing directory is the goal
        try:
            shutil.rmtree("./chroma_store")
            logging.info("Cleaned up ChromaDB storage directory")
        except Exception as e:
            logging.error(f"Failed to clean up ChromaDB storage: {e}")
    
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

app = FastAPI(
    title="GitHub Repo Intelligence Agent",
    description="AI-powered GitHub repository analysis and Q&A system",
    version="0.1.0",
    lifespan=lifespan
)

# Enable CORS for hackathon (allow all origins)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingestion"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])
app.include_router(user.router, prefix="/api/user", tags=["user"])
from app.api import auth
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "github-repo-intelligence-agent"}
