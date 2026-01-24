import logging
import asyncio
from datetime import datetime, timedelta
from app.core.session import session_manager
from app.vector.chroma import ChromaClient

logger = logging.getLogger(__name__)
chroma_client = ChromaClient()

SESSION_TTL_MINUTES = 30
CLEANUP_INTERVAL_SECONDS = 600  # 10 minutes


def cleanup_session(session_id: str) -> None:
    """
    Cleanup a session and its associated data.
    
    Args:
        session_id: Session identifier to cleanup
    """
    logger.info(f"Cleanup requested for session: {session_id}")
    
    # 1. Remove ChromaDB collection
    try:
        chroma_client.cleanup_session(session_id)
    except Exception as e:
        logger.error(f"Error cleaning up ChromaDB for session {session_id}: {e}")
        
    # 2. Remove session from memory
    session_manager.delete_session(session_id)
    logger.info(f"Session {session_id} removed from memory")


async def cleanup_expired_sessions():
    """Check for and remove expired sessions."""
    logger.info("Running scheduled session cleanup")
    try:
        sessions = session_manager.get_all_sessions()
        now = datetime.now()
        
        # Create list to avoid modification during iteration
        session_ids_to_remove = []
        
        for session_id, session_data in sessions.items():
            try:
                # Use last_accessed if available, else created_at
                last_activity_str = session_data.get("last_accessed") or session_data.get("created_at")
                
                if last_activity_str:
                    last_activity = datetime.fromisoformat(last_activity_str)
                    age = now - last_activity
                    
                    # Check against TTL
                    if age > timedelta(minutes=SESSION_TTL_MINUTES):
                        logger.info(f"Session {session_id} expired (inactive for: {age}). marking for cleanup.")
                        session_ids_to_remove.append(session_id)
            except Exception as e:
                logger.error(f"Error checking session {session_id} expiry: {e}")
                
        # Perform cleanup
        for session_id in session_ids_to_remove:
            cleanup_session(session_id)
            
    except Exception as e:
        logger.error(f"Error during overall cleanup: {e}")


async def start_cleanup_loop():
    """Start the background cleanup loop."""
    logger.info("Starting background cleanup loop")
    while True:
        try:
            await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
            await cleanup_expired_sessions()
        except asyncio.CancelledError:
            logger.info("Cleanup loop cancelled")
            break
        except Exception as e:
            logger.error(f"Error in cleanup loop: {e}")
            await asyncio.sleep(60)  # Wait a bit before retrying on error
