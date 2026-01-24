"""GitHub repository loader and cloner."""

import os
import tempfile
import shutil
import logging
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from git import Repo, GitCommandError
from git.exc import GitError

logger = logging.getLogger(__name__)

# Constants
MAX_REPO_SIZE_MB = 50  # Hard limit for total repo size
CLONE_TIMEOUT_SECONDS = 30  # Timeout for cloning operation


class CloneTimeoutError(Exception):
    """Raised when repo cloning exceeds timeout."""
    pass


def load_github_repo(repo_url: str, session_id: str) -> Dict[str, Any]:
    """
    Clone and preprocess a GitHub repository.
    
    This function:
    - Clones the repository to a temporary directory
    - Validates repo size
    - Extracts file structure and metadata
    - Returns repository information
    
    Args:
        repo_url: GitHub repository URL (e.g., https://github.com/user/repo)
        session_id: Session identifier for this ingestion
        
    Returns:
        Dictionary containing:
            - repo_path: Local path to cloned repository
            - repo_name: Repository name
            - branch: Branch that was cloned
            - file_count: Total number of files
            - total_size_mb: Total size in MB
            
    Raises:
        ValueError: If repo URL is invalid
        CloneTimeoutError: If cloning exceeds timeout
        GitError: If cloning fails
        RuntimeError: If repo size exceeds limits
    """
    # Validate and normalize repo URL
    repo_url = _normalize_repo_url(repo_url)
    if not repo_url:
        raise ValueError(f"Invalid GitHub repository URL: {repo_url}")
    
    # Create temporary directory for this session
    temp_dir = Path(tempfile.gettempdir()) / "repo_ingestion" / session_id
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    repo_path = temp_dir / "repo"
    
    try:
        logger.info(f"Cloning repository: {repo_url} to {repo_path}")
        
        # Clone repository with timeout handling
        # Try main branch first, fallback to master
        branch = None
        clone_success = False
        clone_error = None
        
        def clone_worker():
            nonlocal branch, clone_success, clone_error
            try:
                try:
                    Repo.clone_from(repo_url, str(repo_path), branch="main", depth=1)
                    branch = "main"
                    logger.info("Cloned from 'main' branch")
                    clone_success = True
                except GitCommandError:
                    try:
                        Repo.clone_from(repo_url, str(repo_path), branch="master", depth=1)
                        branch = "master"
                        logger.info("Cloned from 'master' branch")
                        clone_success = True
                    except GitCommandError:
                        # If both fail, clone default branch
                        repo = Repo.clone_from(repo_url, str(repo_path), depth=1)
                        branch = repo.active_branch.name
                        logger.info(f"Cloned from default branch: {branch}")
                        clone_success = True
            except Exception as e:
                clone_error = e
        
        # Run clone in a thread with timeout
        clone_thread = threading.Thread(target=clone_worker)
        clone_thread.daemon = True
        clone_thread.start()
        clone_thread.join(timeout=CLONE_TIMEOUT_SECONDS)
        
        if clone_thread.is_alive():
            # Thread is still running, timeout occurred
            # Note: On Windows, this won't actually interrupt the git process,
            # but will detect the timeout and raise an error
            if repo_path.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise CloneTimeoutError(f"Repository cloning exceeded {CLONE_TIMEOUT_SECONDS} seconds")
        
        if not clone_success:
            if clone_error:
                raise clone_error
            raise GitCommandError("clone", "Failed to clone repository")
        
        # Calculate repo size
        total_size = _calculate_directory_size(repo_path)
        total_size_mb = total_size / (1024 * 1024)
        
        logger.info(f"Repository size: {total_size_mb:.2f} MB")
        
        # Check size limit
        if total_size_mb > MAX_REPO_SIZE_MB:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise RuntimeError(
                f"Repository size ({total_size_mb:.2f} MB) exceeds maximum allowed size "
                f"({MAX_REPO_SIZE_MB} MB)"
            )
        
        # Extract repo name from URL
        repo_name = _extract_repo_name(repo_url)
        
        # Count files
        file_count = sum(1 for _ in repo_path.rglob("*") if _.is_file())
        
        logger.info(f"Repository cloned successfully: {repo_name}, {file_count} files")
        
        return {
            "repo_path": str(repo_path),
            "repo_name": repo_name,
            "repo_url": repo_url,
            "branch": branch,
            "file_count": file_count,
            "total_size_mb": total_size_mb
        }
        
    except CloneTimeoutError as e:
        # Cleanup on timeout
        if repo_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Clone timeout: {str(e)}")
        raise
    except (GitError, GitCommandError) as e:
        # Cleanup on error
        if repo_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Git clone error: {str(e)}")
        raise ValueError(f"Failed to clone repository: {str(e)}")
    except Exception as e:
        # Cleanup on any other error
        if repo_path.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        logger.error(f"Unexpected error during clone: {str(e)}")
        raise


def _normalize_repo_url(url: str) -> Optional[str]:
    """
    Normalize GitHub repository URL.
    
    Accepts:
    - https://github.com/user/repo
    - http://github.com/user/repo
    - github.com/user/repo
    - git@github.com:user/repo.git
    
    Returns normalized URL or None if invalid.
    """
    url = url.strip()
    
    # Remove .git suffix if present
    if url.endswith('.git'):
        url = url[:-4]
    
    # Handle SSH format
    if url.startswith('git@github.com:'):
        url = url.replace('git@github.com:', 'https://github.com/')
    
    # Handle missing protocol
    if url.startswith('github.com/'):
        url = 'https://' + url
    
    # Validate GitHub URL format
    if url.startswith('https://github.com/') or url.startswith('http://github.com/'):
        parts = url.split('/')
        if len(parts) >= 5 and parts[3] and parts[4]:
            return url
    
    return None


def _extract_repo_name(url: str) -> str:
    """Extract repository name from URL."""
    url = _normalize_repo_url(url) or url
    parts = url.rstrip('/').split('/')
    if len(parts) >= 2:
        return f"{parts[-2]}/{parts[-1]}"
    return "unknown"


def _calculate_directory_size(directory: Path) -> int:
    """
    Calculate total size of directory in bytes.
    
    Args:
        directory: Path to directory
        
    Returns:
        Total size in bytes
    """
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(directory):
            for filename in filenames:
                filepath = Path(dirpath) / filename
                try:
                    total_size += filepath.stat().st_size
                except (OSError, FileNotFoundError):
                    # Skip files that can't be accessed
                    continue
    except Exception as e:
        logger.warning(f"Error calculating directory size: {str(e)}")
    
    return total_size


def get_repo_structure(repo_path: str) -> list:
    """
    Extract repository file structure.
    
    Args:
        repo_path: Local path to cloned repository
        
    Returns:
        List of file paths (relative to repo root)
    """
    repo_path_obj = Path(repo_path)
    file_list = []
    
    try:
        for file_path in repo_path_obj.rglob("*"):
            if file_path.is_file():
                # Get relative path from repo root
                try:
                    relative_path = file_path.relative_to(repo_path_obj)
                    file_list.append(str(relative_path))
                except ValueError:
                    # Skip if can't get relative path
                    continue
    except Exception as e:
        logger.error(f"Error extracting repo structure: {str(e)}")
    
    return sorted(file_list)


def cleanup_repo_directory(session_id: str) -> None:
    """
    Clean up temporary repository directory for a session.
    
    Args:
        session_id: Session identifier
    """
    temp_dir = Path(tempfile.gettempdir()) / "repo_ingestion" / session_id
    if temp_dir.exists():
        try:
            shutil.rmtree(temp_dir)
            logger.info(f"Cleaned up repo directory for session: {session_id}")
        except Exception as e:
            logger.warning(f"Failed to cleanup repo directory for session {session_id}: {str(e)}")
