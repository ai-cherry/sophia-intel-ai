import hashlib
from pathlib import Path
from typing import Any, Optional


def chunk_code(
    content: str, filepath: str, max_chunk_size: int = 1500, overlap_size: int = 200
) -> list[dict[str, Any]]:
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
    lines = content.split("\n")
    chunks = []
    current_chunk = []
    current_size = 0
    start_line = 1

    for i, line in enumerate(lines, 1):
        line_size = len(line) + 1  # +1 for newline

        if current_size + line_size > max_chunk_size and current_chunk:
            chunk_content = "\n".join(current_chunk)
            chunks.append(
                {
                    "content": chunk_content,
                    "filepath": filepath,
                    "language": _detect_language(filepath),
                    "start_line": start_line,
                    "end_line": i - 1,
                }
            )

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
        chunks.append(
            {
                "content": "\n".join(current_chunk),
                "filepath": filepath,
                "language": _detect_language(filepath),
                "start_line": start_line,
                "end_line": len(lines),
            }
        )

    return chunks


def chunk_document(
    content: str,
    title: str,
    source: str,
    max_chunk_size: int = 2000,
    overlap_size: int = 200,
) -> list[dict[str, Any]]:
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
            last_period = content.rfind(".", start, end)
            if last_period > start + max_chunk_size // 2:
                end = last_period + 1

        chunk_content = content[start:end]
        chunks.append(
            {
                "content": chunk_content,
                "title": title,
                "source": source,
                "metadata": f"chunk_{len(chunks) + 1}",
            }
        )

        start = max(start + 1, end - overlap_size)

    return chunks


def _detect_language(filepath: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "javascript",
        ".tsx": "typescript",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".cs": "csharp",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".r": "r",
        ".m": "matlab",
        ".sh": "bash",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".xml": "xml",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
    }

    for ext, lang in ext_map.items():
        if filepath.lower().endswith(ext):
            return lang
    return "unknown"


def produce_chunks_for_index(
    filepath: str, content: Optional[str] = None, priority: Optional[str] = None
) -> tuple[list[str], list[str], list[dict]]:
    """
    Produce chunks ready for indexing with IDs, texts, and payloads.

    Args:
        filepath: Path to the file
        content: File content (will read if not provided)
        priority: Priority level for routing (high/medium/low)

    Returns:
        Tuple of (ids, texts, payloads) ready for upsert_chunks_dual
    """
    if content is None:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

    # Generate chunks
    chunks = chunk_code(content, filepath)

    ids = []
    texts = []
    payloads = []

    for _i, chunk in enumerate(chunks):
        # Generate stable chunk ID
        chunk_data = f"{filepath}:{chunk['start_line']}:{chunk['end_line']}"
        chunk_id = hashlib.sha256(chunk_data.encode()).hexdigest()[:16]

        ids.append(chunk_id)
        texts.append(chunk["content"])
        payloads.append(
            {
                "path": filepath,
                "lang": chunk["language"],
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "chunk_id": chunk_id,
                "priority": priority or _infer_priority(filepath, chunk["language"]),
            }
        )

    return ids, texts, payloads


def discover_source_files(
    root_dir: str = ".",
    include_patterns: Optional[list[str]] = None,
    exclude_patterns: Optional[list[str]] = None,
) -> list[str]:
    """
    Discover source files for indexing.

    Args:
        root_dir: Root directory to search
        include_patterns: File patterns to include (e.g., ["*.py", "*.ts"])
        exclude_patterns: Patterns to exclude (e.g., ["*test*", "*.min.js"])

    Returns:
        List of file paths to index
    """
    if include_patterns is None:
        include_patterns = [
            "*.py",
            "*.js",
            "*.ts",
            "*.jsx",
            "*.tsx",
            "*.java",
            "*.cpp",
            "*.c",
            "*.cs",
            "*.go",
            "*.rs",
            "*.rb",
            "*.php",
            "*.swift",
            "*.kt",
        ]

    if exclude_patterns is None:
        exclude_patterns = [
            "*test*",
            "*spec*",
            "*.min.js",
            "*vendor*",
            "*node_modules*",
            "*__pycache__*",
            "*.pyc",
            "*dist/*",
            "*build/*",
            "*target/*",
        ]

    files = []
    root = Path(root_dir)

    for pattern in include_patterns:
        for filepath in root.rglob(pattern):
            # Check exclusions
            skip = False
            for exc in exclude_patterns:
                if filepath.match(exc):
                    skip = True
                    break

            if not skip and filepath.is_file():
                # Check file size (skip very large files)
                if filepath.stat().st_size < 500_000:  # 500KB limit
                    files.append(str(filepath))

    return sorted(set(files))


def _infer_priority(filepath: str, language: str) -> str:
    """
    Infer chunk priority based on file characteristics.

    Args:
        filepath: File path
        language: Detected language

    Returns:
        Priority level (high/medium/low)
    """
    # High priority patterns
    high_priority = [
        "main",
        "index",
        "app",
        "core",
        "api",
        "schema",
        "model",
        "config",
        "settings",
    ]

    # Low priority patterns
    low_priority = [
        "test",
        "spec",
        "mock",
        "fixture",
        "example",
        "demo",
        "sample",
        "docs",
        "readme",
    ]

    filepath_lower = filepath.lower()

    # Check for high priority indicators
    for pattern in high_priority:
        if pattern in filepath_lower:
            return "high"

    # Check for low priority indicators
    for pattern in low_priority:
        if pattern in filepath_lower:
            return "low"

    # Complex languages get higher priority
    if language in ["rust", "cpp", "java", "scala"]:
        return "high"

    return "medium"
