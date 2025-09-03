from __future__ import annotations
import ast
from pathlib import Path
from typing import Iterable, Dict, List, Optional, Any
import re


def iter_files(root: str, exts: tuple[str,...] = (".py", ".ts", ".tsx", ".js", ".md")) -> Iterable[Path]:
    p = Path(root)
    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in exts:
            yield f


def simple_chunks(text: str, max_chars: int = 2000, overlap: int = 200) -> List[str]:
    """Simple text chunking with overlap"""
    out: List[str] = []
    i = 0
    n = len(text)
    while i < n:
        out.append(text[i:i+max_chars])
        i += max(1, max_chars - overlap)
    return out


class ASTAwareChunker:
    """Smart code chunking that respects AST structure"""
    
    def __init__(self, max_chunk_size: int = 2000, target_chunk_size: int = 1500):
        self.max_chunk_size = max_chunk_size
        self.target_chunk_size = target_chunk_size
    
    def chunk_python(self, code: str, file_path: str = "") -> List[Dict[str, Any]]:
        """Chunk Python code based on AST structure"""
        chunks = []
        
        try:
            tree = ast.parse(code)
            
            # Extract top-level elements
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    chunk_info = self._extract_node_chunk(node, code, file_path)
                    if chunk_info:
                        chunks.append(chunk_info)
            
            # If no AST chunks or code is too small, fall back to simple chunking
            if not chunks or len(code) < self.target_chunk_size:
                return self._fallback_chunk(code, file_path, "python")
                
        except SyntaxError:
            # If AST parsing fails, use fallback
            return self._fallback_chunk(code, file_path, "python")
        
        return chunks
    
    def chunk_javascript(self, code: str, file_path: str = "") -> List[Dict[str, Any]]:
        """Chunk JavaScript/TypeScript code using regex patterns"""
        chunks = []
        
        # Patterns for JS/TS functions and classes
        patterns = [
            (r'(export\s+)?(async\s+)?function\s+\w+\s*\([^)]*\)\s*\{[^}]*\}', 'function'),
            (r'(export\s+)?class\s+\w+\s*(extends\s+\w+)?\s*\{[^}]*\}', 'class'),
            (r'(export\s+)?const\s+\w+\s*=\s*(async\s*)?\([^)]*\)\s*=>\s*\{[^}]*\}', 'arrow_function'),
            (r'(export\s+)?interface\s+\w+\s*\{[^}]*\}', 'interface'),
        ]
        
        for pattern, chunk_type in patterns:
            for match in re.finditer(pattern, code, re.DOTALL):
                chunk_text = match.group(0)
                if len(chunk_text) <= self.max_chunk_size:
                    chunks.append({
                        'text': chunk_text,
                        'type': chunk_type,
                        'file': file_path,
                        'start_line': code[:match.start()].count('\n') + 1,
                        'end_line': code[:match.end()].count('\n') + 1,
                        'metadata': {
                            'language': 'javascript',
                            'size': len(chunk_text)
                        }
                    })
        
        if not chunks:
            return self._fallback_chunk(code, file_path, "javascript")
        
        return chunks
    
    def chunk_markdown(self, text: str, file_path: str = "") -> List[Dict[str, Any]]:
        """Chunk Markdown by headers and sections"""
        chunks = []
        sections = re.split(r'\n(?=#)', text)
        
        for section in sections:
            if not section.strip():
                continue
                
            # Extract header level and title
            header_match = re.match(r'^(#+)\s+(.+)', section)
            if header_match:
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                
                # Split large sections
                if len(section) > self.max_chunk_size:
                    sub_chunks = simple_chunks(section, self.target_chunk_size, 200)
                    for i, sub_chunk in enumerate(sub_chunks):
                        chunks.append({
                            'text': sub_chunk,
                            'type': 'markdown_section',
                            'file': file_path,
                            'metadata': {
                                'header_level': level,
                                'title': f"{title} (part {i+1})",
                                'language': 'markdown'
                            }
                        })
                else:
                    chunks.append({
                        'text': section,
                        'type': 'markdown_section',
                        'file': file_path,
                        'metadata': {
                            'header_level': level,
                            'title': title,
                            'language': 'markdown'
                        }
                    })
        
        if not chunks:
            return self._fallback_chunk(text, file_path, "markdown")
        
        return chunks
    
    def chunk_file(self, file_path: Path) -> List[Dict[str, Any]]:
        """Chunk a file based on its type"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return []
        
        suffix = file_path.suffix.lower()
        
        if suffix == '.py':
            return self.chunk_python(content, str(file_path))
        elif suffix in ['.js', '.jsx', '.ts', '.tsx']:
            return self.chunk_javascript(content, str(file_path))
        elif suffix in ['.md', '.markdown']:
            return self.chunk_markdown(content, str(file_path))
        else:
            # Default to simple chunking for unknown types
            return self._fallback_chunk(content, str(file_path), suffix[1:] if suffix else "text")
    
    def _extract_node_chunk(self, node: ast.AST, source: str, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract a chunk from an AST node"""
        if not hasattr(node, 'lineno') or not hasattr(node, 'end_lineno'):
            return None
        
        lines = source.split('\n')
        start_line = node.lineno - 1
        end_line = node.end_lineno
        
        chunk_lines = lines[start_line:end_line]
        chunk_text = '\n'.join(chunk_lines)
        
        # Skip if too large
        if len(chunk_text) > self.max_chunk_size:
            # Try to extract just the signature/docstring for large functions/classes
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                sig_lines = lines[start_line:min(start_line + 10, end_line)]
                chunk_text = '\n'.join(sig_lines) + '\n    # ... [truncated]'
            elif isinstance(node, ast.ClassDef):
                # Get class definition and first few methods
                sig_lines = lines[start_line:min(start_line + 20, end_line)]
                chunk_text = '\n'.join(sig_lines) + '\n    # ... [truncated]'
            else:
                return None
        
        node_type = type(node).__name__.lower()
        node_name = getattr(node, 'name', 'unknown')
        
        return {
            'text': chunk_text,
            'type': node_type,
            'name': node_name,
            'file': file_path,
            'start_line': node.lineno,
            'end_line': node.end_lineno,
            'metadata': {
                'language': 'python',
                'size': len(chunk_text),
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'decorators': [d.id for d in node.decorator_list if hasattr(d, 'id')] if hasattr(node, 'decorator_list') else []
            }
        }
    
    def _fallback_chunk(self, text: str, file_path: str, language: str) -> List[Dict[str, Any]]:
        """Fallback to simple chunking when AST parsing fails"""
        simple = simple_chunks(text, self.target_chunk_size, 200)
        return [
            {
                'text': chunk,
                'type': 'text_chunk',
                'file': file_path,
                'metadata': {
                    'language': language,
                    'chunk_index': i,
                    'total_chunks': len(simple),
                    'size': len(chunk)
                }
            }
            for i, chunk in enumerate(simple)
        ]


# Convenience function for backwards compatibility
def ast_aware_chunks(file_path: Path, max_size: int = 2000) -> List[Dict[str, Any]]:
    """Get AST-aware chunks from a file"""
    chunker = ASTAwareChunker(max_chunk_size=max_size)
    return chunker.chunk_file(file_path)