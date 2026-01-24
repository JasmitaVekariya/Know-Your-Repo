"""Token counting utilities."""

import tiktoken


# Use cl100k_base encoding (used by GPT-4, good approximation for most models)
_encoding = None


def _get_encoding():
    """Get or create tiktoken encoding."""
    global _encoding
    if _encoding is None:
        try:
            _encoding = tiktoken.get_encoding("cl100k_base")
        except Exception:
            # Fallback to approximate if tiktoken fails
            _encoding = None
    return _encoding


def count_tokens(text: str) -> int:
    """
    Count tokens in text using tiktoken.
    
    Uses cl100k_base encoding as a good approximation for most models.
    Falls back to character-based estimation if tiktoken is unavailable.
    
    Args:
        text: Input text to count tokens for
        
    Returns:
        Number of tokens
    """
    encoding = _get_encoding()
    if encoding:
        try:
            return len(encoding.encode(text))
        except Exception:
            # Fallback to character-based estimation
            return len(text) // 4  # Rough approximation: ~4 chars per token
    else:
        # Fallback: rough approximation
        return len(text) // 4
