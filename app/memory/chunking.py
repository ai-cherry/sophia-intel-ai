from typing import List, Dict, Any
import re

def chunk_code(
    content: str, 
    filepath: str,
    max_chunk_size: int = 1500,
    overlap_size: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk code into overlapping segments.
    
    Args:
        content: The code content to chunk
        filepath: Path to the code file
        max_chunk_size: Maximum size of each chunk in characters
        overlap_size: Number of characters to overlap between chunks
    
    Returns:
        List of code chunks with metadata
    """
    lines = content.split('\n')
    chunks = []
    current_chunk = []
    current_size = 0
    start_line = 1
    
    for i, line in enumerate(lines, 1):
        line_size = len(line) + 1  # +1 for newline
        
        if current_size + line_size > max_chunk_size and current_chunk:
            chunk_content = '\n'.join(current_chunk)
            chunks.append({
                "content": chunk_content,
                "filepath": filepath,
                "language": _detect_language(filepath),
                "start_line": start_line,
                "end_line": i - 1
            })
            
            # Calculate overlap
            overlap_lines = []
            overlap_size_count = 0
            for j in range(len(current_chunk) - 1, -1, -1):
                line_len = len(current_chunk[j]) + 1
                if overlap_size_count + line_len <= overlap_size:
                    overlap_lines.insert(0, current_chunk[j])
                    overlap_size_count += line_len
                else:
                    break
            
            current_chunk = overlap_lines
            current_size = overlap_size_count
            start_line = i - len(overlap_lines)
        
        current_chunk.append(line)
        current_size += line_size
    
    if current_chunk:
        chunks.append({
            "content": '\n'.join(current_chunk),
            "filepath": filepath,
            "language": _detect_language(filepath),
            "start_line": start_line,
            "end_line": len(lines)
        })
    
    return chunks

def chunk_document(
    content: str,
    title: str,
    source: str,
    max_chunk_size: int = 2000,
    overlap_size: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk document into overlapping segments.
    
    Args:
        content: The document content to chunk
        title: Document title
        source: Document source
        max_chunk_size: Maximum size of each chunk in characters
        overlap_size: Number of characters to overlap between chunks
    
    Returns:
        List of document chunks with metadata
    """
    chunks = []
    start = 0
    
    while start < len(content):
        end = min(start + max_chunk_size, len(content))
        
        # Try to break at sentence boundary
        if end < len(content):
            last_period = content.rfind('.', start, end)
            if last_period > start + max_chunk_size // 2:
                end = last_period + 1
        
        chunk_content = content[start:end]
        chunks.append({
            "content": chunk_content,
            "title": title,
            "source": source,
            "metadata": f"chunk_{len(chunks) + 1}"
        })
        
        start = max(start + 1, end - overlap_size)
    
    return chunks

def _detect_language(filepath: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        '.py': 'python',
        '.js': 'javascript',
        '.ts': 'typescript',
        '.jsx': 'javascript',
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
        '.m': 'matlab',
        '.sh': 'bash',
        '.sql': 'sql',
        '.html': 'html',
        '.css': 'css',
        '.xml': 'xml',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
        '.md': 'markdown'
    }
    
    for ext, lang in ext_map.items():
        if filepath.lower().endswith(ext):
            return lang
    return 'unknown'