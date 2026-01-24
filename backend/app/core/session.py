"""Session management for repository ingestion and chat sessions."""

import uuid
from typing import Dict, Optional
from datetime import datetime


class SessionManager:
    """Manages in-memory sessions. Will later map to ChromaDB."""
    
    def __init__(self):
        """Initialize session manager with empty store."""
        self._sessions: Dict[str, dict] = {}
    
    def create_session(self, repo_url: Optional[str] = None) -> str:
        """
        Create a new session.
        
        Args:
            repo_url: Optional repository URL associated with session
            
        Returns:
            Session ID (UUID string)
        """
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = {
            "session_id": session_id,
            "repo_url": repo_url,
            "created_at": datetime.now().isoformat(),
            "status": "initialized"
        }
        return session_id
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """
        Get session by ID.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None if not found
        """
        return self._sessions.get(session_id)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def update_session(self, session_id: str, **kwargs) -> bool:
        """
        Update session data.
        
        Args:
            session_id: Session identifier
            **kwargs: Key-value pairs to update
            
        Returns:
            True if updated, False if session not found
        """
        if session_id in self._sessions:
            self._sessions[session_id].update(kwargs)
            return True
        return False
    
    def store_manifest(self, session_id: str, manifest: dict) -> bool:
        """
        Store repository manifest for a session.
        
        Args:
            session_id: Session identifier
            manifest: Manifest dictionary
            
        Returns:
            True if stored, False if session not found
        """
        if session_id in self._sessions:
            self._sessions[session_id]['manifest'] = manifest
            return True
        return False
    
    def store_chunks(self, session_id: str, chunks: list) -> bool:
        """
        Store file chunks for a session.
        
        Args:
            session_id: Session identifier
            chunks: List of chunk dictionaries
            
        Returns:
            True if stored, False if session not found
        """
        if session_id in self._sessions:
            self._sessions[session_id]['chunks'] = chunks
            return True
        return False
    
    def get_manifest(self, session_id: str) -> Optional[dict]:
        """
        Get repository manifest for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Manifest dictionary or None
        """
        session = self.get_session(session_id)
        if session:
            return session.get('manifest')
        return None
    
    def get_chunks(self, session_id: str) -> Optional[list]:
        """
        Get file chunks for a session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            List of chunks or None
        """
        session = self.get_session(session_id)
        if session:
            return session.get('chunks')
        return None

    def get_all_sessions(self) -> Dict[str, dict]:
        """
        Get all active sessions.
        
        Returns:
            Dictionary of all session objects
        """
        return self._sessions


# Global session manager instance
session_manager = SessionManager()
