"""Mermaid diagram validation and sanitization utilities."""

import re
import logging

logger = logging.getLogger(__name__)


def sanitize_mermaid_diagram(diagram_text: str) -> str:
    """
    Sanitize and fix common Mermaid syntax errors.
    
    Args:
        diagram_text: Raw Mermaid diagram text
        
    Returns:
        Sanitized diagram text or empty string if unfixable
    """
    if not diagram_text or not diagram_text.strip():
        return ""
    
    lines = diagram_text.strip().split('\n')
    sanitized_lines = []
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        # Fix first line: ensure it's "flowchart TD"
        if i == 0 or (i == 1 and not sanitized_lines):
            if 'graph' in line.lower() or 'flowchart' in line.lower():
                sanitized_lines.append("flowchart TD")
                continue
        
        # Remove style statements (they cause errors)
        if line.startswith('style '):
            logger.warning(f"Removed style statement: {line}")
            continue
            
        # Remove subgraph statements (simplify)
        if line.startswith('subgraph ') or line == 'end':
            logger.warning(f"Removed subgraph: {line}")
            continue
        
        # Fix node labels: remove quotes and problematic characters
        # Pattern: A['text'] or A["text"] or A[text's] or A[text (v2)]
        line = re.sub(r'\[(["\'])([^"\']+)\1\]', r'[\2]', line)  # Remove quotes
        line = re.sub(r'\[([^\]]*)["\']([^\]]*)\]', r'[\1\2]', line)  # Remove apostrophes
        line = re.sub(r'\[([^\]]*)\(([^\)]*)\)([^\]]*)\]', r'[\1 \2 \3]', line)  # Remove parentheses
        
        # Fix incomplete arrows: C -- or D -> without destination
        if re.search(r'--\s*$', line) or re.search(r'->\s*$', line):
            logger.warning(f"Skipped incomplete arrow: {line}")
            continue
        
        # Fix arrow syntax: ensure proper spacing
        line = re.sub(r'-->', ' --> ', line)
        line = re.sub(r'\s+', ' ', line)  # Normalize whitespace
        
        sanitized_lines.append(line)
    
    # Ensure we have at least flowchart TD
    if not sanitized_lines or sanitized_lines[0] != "flowchart TD":
        sanitized_lines.insert(0, "flowchart TD")
    
    # Limit to 8 nodes maximum (count lines with -->)
    arrow_lines = [l for l in sanitized_lines if '-->' in l]
    if len(arrow_lines) > 8:
        logger.warning(f"Diagram too complex ({len(arrow_lines)} arrows), truncating to 8")
        sanitized_lines = [sanitized_lines[0]] + arrow_lines[:8]
    
    result = '\n'.join(sanitized_lines)
    logger.info(f"Sanitized Mermaid diagram: {len(lines)} -> {len(sanitized_lines)} lines")
    
    return result


def extract_mermaid_blocks(text: str) -> list[tuple[str, str]]:
    """
    Extract all Mermaid code blocks from markdown text.
    
    Args:
        text: Markdown text containing mermaid blocks
        
    Returns:
        List of tuples (original_block, sanitized_block)
    """
    pattern = r'```mermaid\n(.*?)\n```'
    matches = re.findall(pattern, text, re.DOTALL)
    
    results = []
    for match in matches:
        original = match
        sanitized = sanitize_mermaid_diagram(match)
        results.append((original, sanitized))
    
    return results


def replace_mermaid_blocks(text: str) -> str:
    """
    Replace all Mermaid blocks in text with sanitized versions.
    
    Args:
        text: Markdown text containing mermaid blocks
        
    Returns:
        Text with sanitized mermaid blocks
    """
    blocks = extract_mermaid_blocks(text)
    
    result = text
    for original, sanitized in blocks:
        if sanitized:
            # Replace the original block content with sanitized version
            result = result.replace(
                f'```mermaid\n{original}\n```',
                f'```mermaid\n{sanitized}\n```'
            )
        else:
            # Remove the block entirely if it couldn't be sanitized
            result = result.replace(f'```mermaid\n{original}\n```', '')
            logger.warning("Removed unsanitizable Mermaid block")
    
    return result
