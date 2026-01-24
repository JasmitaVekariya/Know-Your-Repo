"""Text chunking utilities for splitting repository files into manageable pieces."""

import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
from app.utils.token_counter import count_tokens

logger = logging.getLogger(__name__)

# Constants
TARGET_CHUNK_SIZE_TOKENS = 500  # Target chunk size (400-600 range)
MIN_CHUNK_SIZE_TOKENS = 400
MAX_CHUNK_SIZE_TOKENS = 600


def detect_language(file_path: Path) -> str:
    """
    Detect programming language from file extension.
    
    Args:
        file_path: Path to file
        
    Returns:
        Language name (e.g., 'python', 'javascript', 'typescript')
    """
    extension_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
        '.scala': 'scala',
        '.r': 'r',
        '.m': 'objective-c',
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'bash',
        '.fish': 'bash',
        '.ps1': 'powershell',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.scss': 'css',
        '.sass': 'css',
        '.less': 'css',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.md': 'markdown',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.xml': 'xml',
        '.toml': 'toml',
        '.ini': 'ini',
        '.conf': 'config',
        '.config': 'config',
    }
    
    ext = file_path.suffix.lower()
    return extension_map.get(ext, 'unknown')


def detect_module_type(file_path: Path, content: str) -> str:
    """
    Detect module type (core, config, test, doc).
    
    Args:
        file_path: Path to file
        content: File content (first few lines)
        
    Returns:
        Module type: 'core', 'config', 'test', or 'doc'
    """
    path_str = str(file_path).lower()
    name_lower = file_path.name.lower()
    
    # Test files
    if ('test' in path_str or 'spec' in path_str or 
        name_lower.startswith('test_') or 
        name_lower.endswith('_test.py') or
        name_lower.endswith('.test.js') or
        name_lower.endswith('.spec.js')):
        return 'test'
    
    # Config files
    if (name_lower in ['config.py', 'settings.py', 'config.js', 'config.ts',
                       'package.json', 'requirements.txt', 'pom.xml',
                       'build.gradle', 'dockerfile', '.env', '.env.example',
                       'webpack.config.js', 'tsconfig.json', 'jest.config.js'] or
        'config' in path_str or 'settings' in path_str):
        return 'config'
    
    # Documentation
    if (name_lower.endswith('.md') or name_lower in ['readme', 'license', 'changelog', 'contributing'] or
        'doc' in path_str or 'docs' in path_str):
        return 'doc'
    
    # Default to core
    return 'core'


def is_entry_candidate(file_path: Path, content: str) -> bool:
    """
    Determine if file is a potential entry point.
    
    Args:
        file_path: Path to file
        content: File content (first few lines)
        
    Returns:
        True if file is likely an entry point
    """
    name_lower = file_path.name.lower()
    path_str = str(file_path).lower()
    
    # Common entry point names
    entry_names = [
        'main.py', 'app.py', 'index.py', '__main__.py',
        'index.js', 'app.js', 'server.js', 'main.js',
        'index.ts', 'app.ts', 'server.ts', 'main.ts',
        'main.java', 'app.java',
        'main.cpp', 'main.c',
        'main.go', 'main.rs',
        'index.html', 'app.html',
    ]
    
    if name_lower in entry_names:
        return True
    
    # Check for entry point patterns in content
    entry_patterns = [
        r'if\s+__name__\s*==\s*["\']__main__["\']',  # Python
        r'require\(["\']\.\/app["\']',  # Node.js
        r'from\s+.*\s+import\s+app',  # Flask/FastAPI
        r'@app\.',  # Flask decorator
        r'app\.listen\(',  # Express.js
    ]
    
    first_lines = content[:500].lower()  # Check first 500 chars
    for pattern in entry_patterns:
        if re.search(pattern, first_lines):
            return True
    
    # Check if in root or src/main directory
    if (file_path.parent.name in ['', 'src', 'app', 'lib'] or
        'src/main' in path_str or 'src/index' in path_str):
        # Additional check: file should not be too large or in test dir
        if 'test' not in path_str and len(content) < 10000:
            return True
    
    return False


def chunk_file_content(
    content: str,
    file_path: str,
    chunk_size: int = TARGET_CHUNK_SIZE_TOKENS,
    chunk_overlap: int = 50
) -> List[Dict[str, Any]]:
    """
    Split file content into chunks for vectorization.
    
    This function splits content into overlapping chunks, attempting to
    preserve code structure where possible.
    
    Args:
        content: File content as string
        file_path: Path to the source file
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap between chunks in tokens
        
    Returns:
        List of chunk dictionaries with content and metadata
    """
    if not content or not content.strip():
        return []
    
    file_path_obj = Path(file_path)
    language = detect_language(file_path_obj)
    module_type = detect_module_type(file_path_obj, content)
    is_entry = is_entry_candidate(file_path_obj, content)
    
    # Try language-aware chunking first
    if language in ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'go', 'rust']:
        chunks = chunk_code_file(content, file_path, language, chunk_overlap)
    elif language == 'markdown':
        chunks = chunk_markdown_file(content, file_path)
    else:
        # Fallback to generic chunking
        chunks = _chunk_generic(content, file_path, chunk_size, chunk_overlap)
    
    # Add metadata to each chunk
    for chunk in chunks:
        chunk['file_path'] = file_path
        chunk['language'] = language
        chunk['module_type'] = module_type
        chunk['is_entry_candidate'] = is_entry
        if 'entity_name' not in chunk:
            chunk['entity_name'] = ""
    
    return chunks


def chunk_code_file(content: str, file_path: str, language: str, chunk_overlap: int = 50) -> List[Dict[str, Any]]:
    """
    Chunk code files with language-aware splitting.
    
    Attempts to split at function/class boundaries when possible.
    
    Args:
        content: File content as string
        file_path: Path to the source file
        language: Programming language
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    
    # Language-specific patterns for splitting
    # Language-specific patterns for splitting
    # Updated to capture the entity name in the last group
    patterns = {
        'python': [
            (r'^def\s+(\w+)', 'function'),
            (r'^class\s+(\w+)', 'class'),
            (r'^@(\w+)', 'decorator'),
        ],
        'javascript': [
            (r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)', 'function'),
            (r'^(?:export\s+)?class\s+(\w+)', 'class'),
            (r'^(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(', 'arrow'),
            (r'^(?:export\s+)?const\s+(\w+)\s*=\s*\{', 'object'),
        ],
        'typescript': [
            (r'^(?:export\s+)?(?:async\s+)?function\s+(\w+)', 'function'),
            (r'^(?:export\s+)?(?:abstract\s+)?class\s+(\w+)', 'class'),
            (r'^(?:export\s+)?interface\s+(\w+)', 'interface'),
            (r'^(?:export\s+)?type\s+(\w+)', 'type'),
            (r'^(?:export\s+)?const\s+(\w+)\s*[:=]', 'const'),
        ],
        'java': [
            (r'^(?:public|private|protected)?\s*(?:static\s+)?(?:class|interface|enum)\s+(\w+)', 'class'),
            (r'^(?:public|private|protected)?\s*(?:static\s+)?\w+\s+(\w+)\s*\(', 'method'),
        ],
        'cpp': [
            (r'^(?:class|struct|namespace)\s+(\w+)', 'class'),
            (r'^\w+\s+(\w+)::\w+', 'method'),
        ],
        'go': [
            (r'^func\s+(\w+)', 'function'),
            (r'^type\s+(\w+)', 'type'),
            (r'^package\s+(\w+)', 'package'),
        ],
        'rust': [
            (r'^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)', 'function'),
            (r'^(?:pub\s+)?(?:struct|enum|impl|trait)\s+(\w+)', 'type'),
        ],
    }
    
    pattern_list = patterns.get(language, [])
    
    if pattern_list:
        # Split by logical blocks
        lines = content.split('\n')
        current_chunk = []
        current_tokens = 0
        current_entity = None
        
        for line in lines:
            line_tokens = count_tokens(line)
            
            # Check if this line starts a new logical block and extract name
            match = None
            entity_type = None
            
            for pattern, type_name in pattern_list:
                m = re.match(pattern, line)
                if m:
                    match = m
                    entity_type = type_name
                    break
            
            starts_block = match is not None
            
            # If adding this line would exceed max size, finalize current chunk
            if current_tokens + line_tokens > MAX_CHUNK_SIZE_TOKENS and current_chunk:
                chunk_text = '\n'.join(current_chunk)
                # Enrich content with entity name if available
                if current_entity:
                    chunk_text = f"### Entity: {current_entity}\n" + chunk_text
                    
                chunks.append({
                    'content': chunk_text,
                    'start_line': len(chunks) * 100,  # Approximate
                    'end_line': len(chunks) * 100 + len(current_chunk),
                    'entity_name': current_entity or "",
                })
                
                # Start new chunk with overlap
                overlap_lines = _get_overlap_lines(current_chunk, chunk_overlap)
                current_chunk = overlap_lines + [line]
                current_tokens = sum(count_tokens(l) for l in current_chunk)
                
                # Update entity if this line started a new block
                if starts_block:
                     # Try to capture group 1 (name), else use whole match
                    if match.groups():
                        # Find the first non-None group that isn't export/pub/async prefix keywords usually found in group 1/2
                        # This depends on regex. Let's rely on the last group usually being the name or close to it.
                        # Actually, let's just use the full match line as a proxy or refine patterns.
                        # Better approach: Extract name from specific patterns.
                        # For now, let's define that the NAME is the last captured group if multiple, or the first if one.
                        groups = [g for g in match.groups() if g]
                        current_entity = groups[-1] if groups else "unknown"
                    else:
                        current_entity = "block"
                        
            elif starts_block and current_tokens > MIN_CHUNK_SIZE_TOKENS and current_chunk:
                # Start new chunk at logical boundary
                chunk_text = '\n'.join(current_chunk)
                if current_entity:
                    chunk_text = f"### Entity: {current_entity}\n" + chunk_text
                    
                chunks.append({
                    'content': chunk_text,
                    'start_line': len(chunks) * 100,
                    'end_line': len(chunks) * 100 + len(current_chunk),
                    'entity_name': current_entity or "",
                })
                current_chunk = [line]
                current_tokens = line_tokens
                
                # Update entity
                if match.groups():
                    groups = [g for g in match.groups() if g]
                    current_entity = groups[-1] if groups else "unknown"
                else:
                    current_entity = "block"

            else:
                current_chunk.append(line)
                current_tokens += line_tokens
                
                # Capture entity if it's the first line of the file/chunk and we haven't set it
                if starts_block and current_entity is None:
                     if match.groups():
                        groups = [g for g in match.groups() if g]
                        current_entity = groups[-1] if groups else "unknown"
        
        # Add final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'start_line': len(chunks) * 100,
                'end_line': len(chunks) * 100 + len(current_chunk),
            })
    else:
        # Fallback to generic chunking
        return _chunk_generic(content, file_path, TARGET_CHUNK_SIZE_TOKENS, 50)
    
    return chunks


def chunk_markdown_file(content: str, file_path: str) -> List[Dict[str, Any]]:
    """
    Chunk markdown files preserving section structure.
    
    Args:
        content: Markdown content as string
        file_path: Path to the markdown file
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    
    # Split by headers (##, ###, etc.)
    sections = re.split(r'^(#{1,6}\s+.+)$', content, flags=re.MULTILINE)
    
    current_chunk = []
    current_tokens = 0
    
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        
        section_tokens = count_tokens(section)
        
        # If section is a header, check if we should start new chunk
        if re.match(r'^#{1,6}\s+', section):
            if current_tokens > MIN_CHUNK_SIZE_TOKENS and current_chunk:
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    'content': chunk_text,
                    'start_line': len(chunks) * 50,
                    'end_line': len(chunks) * 50 + len(current_chunk),
                })
                current_chunk = [section]
                current_tokens = section_tokens
            else:
                current_chunk.append(section)
                current_tokens += section_tokens
        else:
            # Regular content
            if current_tokens + section_tokens > MAX_CHUNK_SIZE_TOKENS:
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    chunks.append({
                        'content': chunk_text,
                        'start_line': len(chunks) * 50,
                        'end_line': len(chunks) * 50 + len(current_chunk),
                    })
                current_chunk = [section]
                current_tokens = section_tokens
            else:
                current_chunk.append(section)
                current_tokens += section_tokens
    
    # Add final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunks.append({
            'content': chunk_text,
            'start_line': len(chunks) * 50,
            'end_line': len(chunks) * 50 + len(current_chunk),
        })
    
    return chunks


def _chunk_generic(content: str, file_path: str, chunk_size: int, chunk_overlap: int) -> List[Dict[str, Any]]:
    """
    Generic chunking when language-specific chunking is not available.
    
    Args:
        content: File content
        file_path: File path
        chunk_size: Target chunk size in tokens
        chunk_overlap: Overlap in tokens
        
    Returns:
        List of chunk dictionaries
    """
    chunks = []
    lines = content.split('\n')
    
    current_chunk = []
    current_tokens = 0
    
    for line in lines:
        line_tokens = count_tokens(line)
        
        if current_tokens + line_tokens > chunk_size and current_chunk:
            chunk_text = '\n'.join(current_chunk)
            chunks.append({
                'content': chunk_text,
                'start_line': len(chunks) * 100,
                'end_line': len(chunks) * 100 + len(current_chunk),
            })
            
            # Start new chunk with overlap
            overlap_lines = _get_overlap_lines(current_chunk, chunk_overlap)
            current_chunk = overlap_lines + [line]
            current_tokens = sum(count_tokens(l) for l in current_chunk)
        else:
            current_chunk.append(line)
            current_tokens += line_tokens
    
    # Add final chunk
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunks.append({
            'content': chunk_text,
            'start_line': len(chunks) * 100,
            'end_line': len(chunks) * 100 + len(current_chunk),
        })
    
    return chunks


def _get_overlap_lines(lines: List[str], overlap_tokens: int) -> List[str]:
    """
    Get last N lines that approximately match overlap_tokens.
    
    Args:
        lines: List of lines
        overlap_tokens: Target overlap in tokens
        
    Returns:
        List of lines for overlap
    """
    if not lines:
        return []
    
    overlap_lines = []
    overlap_count = 0
    
    # Start from the end
    for line in reversed(lines):
        line_tokens = count_tokens(line)
        if overlap_count + line_tokens <= overlap_tokens:
            overlap_lines.insert(0, line)
            overlap_count += line_tokens
        else:
            break
    
    return overlap_lines
