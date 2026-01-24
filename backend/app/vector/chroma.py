import logging
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import uuid

logger = logging.getLogger(__name__)


class ChromaClient:
    """Client for interacting with ChromaDB vector database."""
    
    def __init__(self, persist_directory: str = "./chroma_store"):
        """
        Initialize ChromaDB client.
        
        Args:
            persist_directory: Directory to persist ChromaDB data
        """
        self.persist_directory = persist_directory
        try:
            self.client = chromadb.PersistentClient(path=persist_directory)
            logger.info(f"Initialized ChromaDB client at {persist_directory}")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise

    def create_session_collection(self, session_id: str) -> None:
        """
        Create a collection for a specific session.
        
        Args:
            session_id: Session identifier
        """
        try:
            self.client.get_or_create_collection(name=session_id)
            logger.info(f"Created/Retrieved collection for session: {session_id}")
        except Exception as e:
            logger.error(f"Failed to create collection for session {session_id}: {e}")
            raise

    def add_chunks(self, session_id: str, chunks: List[Dict[str, Any]]) -> None:
        """
        Add chunks to the session collection.
        
        Args:
            session_id: Session identifier
            chunks: List of chunk dictionaries containing 'content' and metadata
        """
        try:
            collection = self.client.get_collection(name=session_id)
            
            ids = [f"{session_id}_{i}_{str(uuid.uuid4())[:8]}" for i in range(len(chunks))]
            documents = [chunk["content"] for chunk in chunks]
            
            metadatas = []
            for chunk in chunks:
                # Filter metadata to ensure it's flat and compatible
                meta = {
                    "file_path": str(chunk.get("file_path", "")),
                    "language": str(chunk.get("language", "unknown")),
                    "module_type": str(chunk.get("module_type", "unknown")),
                    "start_line": int(chunk.get("start_line", 0)),
                    "end_line": int(chunk.get("end_line", 0))
                }
                metadatas.append(meta)
                
            # Batch add to avoid memory issues and timeouts
            batch_size = 5000
            total_chunks = len(chunks)
            
            for i in range(0, total_chunks, batch_size):
                end_idx = min(i + batch_size, total_chunks)
                batch_documents = documents[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                batch_ids = ids[i:end_idx]
                
                collection.add(
                    documents=batch_documents,
                    metadatas=batch_metadatas,
                    ids=batch_ids
                )
                logger.info(f"Added batch {i}-{end_idx} of {total_chunks} chunks to session {session_id}")
            logger.info(f"Added {len(chunks)} chunks to session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to add chunks to session {session_id}: {e}")
            raise

    def query(self, session_id: str, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Query the session collection.
        
        Args:
            session_id: Session identifier
            query: Query text
            top_k: Number of results to return
            
        Returns:
            List of result chunks with metadata
        """
        try:
            collection = self.client.get_collection(name=session_id)
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
            
            # Format results
            formatted_results = []
            if results["documents"]:
                for i, doc in enumerate(results["documents"][0]):
                    formatted_results.append({
                        "content": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {}
                    })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to query session {session_id}: {e}")
            # If collection doesn't exist or other error, return empty list or raise
            # The requirements say "Query on expired session -> explicit error"
            # But get_collection raises ValueError if not found usually
            raise

    def cleanup_session(self, session_id: str) -> None:
        """
        Delete the collection for a session.
        
        Args:
            session_id: Session identifier
        """
        try:
            try:
                self.client.delete_collection(name=session_id)
                logger.info(f"Deleted collection for session: {session_id}")
            except ValueError:
                logger.warning(f"Collection {session_id} not found during cleanup")
        except Exception as e:
            logger.error(f"Failed to cleanup session {session_id}: {e}")
            raise
