"""Application configuration management."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Application configuration."""
    
    def __init__(self):
        """Initialize configuration. Does not validate on import."""
        self._gemini_api_key: Optional[str] = None
        self._mongo_uri: Optional[str] = None
    
    @property
    def GEMINI_API_KEY(self) -> str:
        """Get Gemini API key from environment."""
        if self._gemini_api_key is None:
            self._gemini_api_key = os.getenv("GEMINI_API_KEY")
            if not self._gemini_api_key:
                raise ValueError(
                    "GEMINI_API_KEY not found in environment variables. "
                    "Please set it in your .env file."
                )
        return self._gemini_api_key
    
    @property
    def MONGO_URI(self) -> str:
        """Get MongoDB URI from environment."""
        if self._mongo_uri is None:
            self._mongo_uri = os.getenv("MONGO_URI")
            if not self._mongo_uri:
                raise ValueError(
                    "MONGO_URI not found in environment variables. "
                    "Please set it in your .env file."
                )
        return self._mongo_uri


# Global config instance
config = Config()
