"""File filtering utilities for repository ingestion."""

import logging
from pathlib import Path
from typing import List, Set, Tuple, Optional

logger = logging.getLogger(__name__)

# Constants
MAX_FILE_SIZE_KB = 5000  # Max file size in KB (5 MB)
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_KB * 1024
MAX_LINES = 20000  # Max lines per file
HARD_STOP_FILE_SIZE_MB = 10  # Hard stop for individual files
HARD_STOP_FILE_SIZE_BYTES = HARD_STOP_FILE_SIZE_MB * 1024 * 1024

# Directories to ignore
IGNORE_DIRECTORIES: Set[str] = {
    "node_modules",
    ".git",
    "dist",
    "build",
    "out",
    "target",
    "venv",
    "__pycache__",
    "coverage",
    ".next",
    ".cache",
    ".venv",
    "env",
    ".env",
    "vendor",
    ".idea",
    ".vscode",
    ".vs",
    "bin",
    "obj",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "htmlcov",
}

# File extensions to ignore
IGNORE_EXTENSIONS: Set[str] = {
    # Images
    ".png", ".jpg", ".jpeg", ".svg", ".gif", ".ico", ".webp", ".bmp",
    # Media
    ".mp4", ".mp3", ".avi", ".mov", ".wav", ".flac", ".ogg",
    # Archives
    ".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar",
    # Lock files
    ".lock",
    # Minified/map files
    ".min.js", ".map", ".min.css",
    # Other
    ".pdf", ".doc", ".docx", ".xls", ".xlsx",
    ".exe", ".dll", ".so", ".dylib",
    ".woff", ".woff2", ".ttf", ".eot",  # Fonts
}


def should_include_file(
    file_path: Path,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Determine if a file should be included in ingestion.
    
    Returns:
        Tuple of (should_include: bool, reason: Optional[str])
        If should_include is False, reason explains why
    """
    file_path_str = str(file_path)
    
    # Check directory exclusions
    parts = file_path.parts
    for part in parts:
        if part in IGNORE_DIRECTORIES:
            return False, f"Directory '{part}' is in ignore list"
    
    # Check file extension
    if file_path.suffix.lower() in IGNORE_EXTENSIONS:
        return False, f"Extension '{file_path.suffix}' is in ignore list"
    
    # Check hard stop file size
    try:
        file_size = file_path.stat().st_size
        if file_size > HARD_STOP_FILE_SIZE_BYTES:
            return False, f"File size ({file_size / (1024*1024):.2f} MB) exceeds hard stop limit ({HARD_STOP_FILE_SIZE_MB} MB)"
    except (OSError, FileNotFoundError):
        return False, "Cannot access file"
    
    # Check custom patterns if provided
    if exclude_patterns:
        for pattern in exclude_patterns:
            if pattern in file_path_str:
                return False, f"Matches exclude pattern: {pattern}"
    
    if include_patterns:
        matched = any(pattern in file_path_str for pattern in include_patterns)
        if not matched:
            return False, "Does not match any include pattern"
    
    return True, None


def get_default_exclude_patterns() -> List[str]:
    """
    Get default patterns to exclude from ingestion.
    
    Returns:
        List of exclusion patterns
    """
    return list(IGNORE_DIRECTORIES)


def filter_files_by_size(file_paths: List[Path], max_size_kb: int = MAX_FILE_SIZE_KB) -> List[Path]:
    """
    Filter out files that exceed size limit.
    """
    max_size_bytes = max_size_kb * 1024
    filtered = []
    
    for file_path in file_paths:
        try:
            file_size = file_path.stat().st_size
            if file_size <= max_size_bytes:
                filtered.append(file_path)
            else:
                logger.debug(f"Skipping large file: {file_path} ({file_size / 1024:.2f} KB)")
        except (OSError, FileNotFoundError):
            logger.warning(f"Cannot access file for size check: {file_path}")
            continue
    
    return filtered


def filter_files_by_lines(file_paths: List[Path], max_lines: int = MAX_LINES) -> List[Path]:
    """
    Filter out files that exceed line count limit.
    """
    filtered = []
    
    for file_path in file_paths:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                line_count = sum(1 for _ in f)
                if line_count <= max_lines:
                    filtered.append(file_path)
                else:
                    logger.debug(f"Skipping file with too many lines: {file_path} ({line_count} lines)")
        except (UnicodeDecodeError, OSError, FileNotFoundError):
            # Skip binary files or files that can't be read
            logger.debug(f"Cannot read file for line count: {file_path}")
            continue
    
    return filtered


def read_file_content(file_path: Path) -> Tuple[Optional[str], bool]:
    """
    Read file content, handling size and line limits.
    """
    try:
        file_size = file_path.stat().st_size
        
        # Hard stop check
        if file_size > HARD_STOP_FILE_SIZE_BYTES:
            return (
                f"[File too large: {file_size / (1024*1024):.2f} MB. Hard stop limit: {HARD_STOP_FILE_SIZE_MB} MB]",
                True
            )
        
        # Check if exceeds processing limits (soft warning/summary)
        exceeds_size = file_size > MAX_FILE_SIZE_BYTES
        
        # Count lines
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            line_count = len(lines)
            exceeds_lines = line_count > MAX_LINES
        
        if exceeds_size or exceeds_lines:
            # Generate summary IF it genuinely exceeds the new high limits
            # But since limits are high, this probably catches extreme outliers
            preview_lines = lines[:50] if lines else []
            preview_text = ''.join(preview_lines)
            
            summary = (
                f"[File summary - Size: {file_size / 1024:.2f} KB, Lines: {line_count}]\n"
                f"Preview (first 50 lines):\n{preview_text}\n"
                f"[Content truncated due to size/line limits]"
            )
            return summary, True
        
        # Return full content
        return ''.join(lines), False
        
    except (UnicodeDecodeError, OSError, FileNotFoundError) as e:
        logger.warning(f"Cannot read file {file_path}: {str(e)}")
        return None, False


def filter_repository_files(repo_path: Path) -> List[Path]:
    """
    Filter all files in repository according to rules.
    
    Args:
        repo_path: Path to repository root
        
    Returns:
        List of file paths that passed all filters
    """
    included_files = []
    
    for file_path in repo_path.rglob("*"):
        if not file_path.is_file():
            continue
        
        should_include, reason = should_include_file(file_path)
        if should_include:
            included_files.append(file_path)
        else:
            logger.debug(f"Excluding file {file_path}: {reason}")
    
    # We rely on read_file_content to handle large files gracefully
    # We do NOT filter by size/lines here anymore to avoid dropping large C files
    # The new read_file_summary will catch anything truly massive (>10MB)
    
    logger.info(f"Filtered repository: {len(included_files)} files included")
    
    return included_files
