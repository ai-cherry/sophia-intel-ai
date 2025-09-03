from __future__ import annotations


def chunk_text(text: str, max_chunk_size: int = 1000, max_chunks: int = 1000) -> list[str]:
    """
    Simple, stable text chunker that splits text into manageable chunks.
    
    This function intelligently splits text while trying to preserve paragraph
    boundaries when possible. It splits by double newlines first to keep
    paragraphs together, then concatenates lines until reaching the chunk size
    limit. For paragraphs exceeding the limit, it falls back to hard splitting.
    
    Args:
        text: The input text to be chunked. Can be any text content including
              code, documentation, or natural language text.
        max_chunk_size: Maximum number of characters per chunk. Defaults to 1000.
                       Chunks may slightly exceed this if needed to avoid breaking
                       words mid-character during hard splits.
        max_chunks: Maximum number of chunks to return. Defaults to 1000.
                   This cap prevents runaway memory usage for extremely large texts.
    
    Returns:
        A list of text chunks, each approximately max_chunk_size characters or less.
        Returns an empty list if the input text is empty or None.
    
    Example:
        >>> text = "This is paragraph one.\\n\\nThis is paragraph two.\\n\\nThis is paragraph three."
        >>> chunks = chunk_text(text, max_chunk_size=30)
        >>> logger.info(chunks[0])
        'This is paragraph one.\\n\\n'
        >>> logger.info(chunks[1])
        'This is paragraph two.\\n\\n'
    
    Note:
        This is intentionally a naive and deterministic implementation.
        For more sophisticated text splitting (e.g., semantic splitting,
        sentence boundary detection), consider upgrading to a specialized
        NLP-based text splitter in the future.
    """
    if not text:
        return []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    # Prefer paragraphs but keep single newlines
    paragraphs = text.split("\n\n")

    for para in paragraphs:
        # Preserve paragraph with its trailing separator when joining
        para_with_sep = para if para.endswith("\n") else para + "\n\n"
        if len(para_with_sep) > max_chunk_size:
            # Hard split long paragraphs
            start = 0
            while start < len(para_with_sep):
                end = start + max_chunk_size
                hard_piece = para_with_sep[start:end]
                if current_len + len(hard_piece) > max_chunk_size and current:
                    chunks.append("".join(current))
                    if len(chunks) >= max_chunks:
                        return chunks
                    current, current_len = [], 0
                current.append(hard_piece)
                current_len += len(hard_piece)
                if current_len >= max_chunk_size:
                    chunks.append("".join(current))
                    if len(chunks) >= max_chunks:
                        return chunks
                    current, current_len = [], 0
                start = end
        else:
            if current_len + len(para_with_sep) > max_chunk_size and current:
                chunks.append("".join(current))
                if len(chunks) >= max_chunks:
                    return chunks
                current, current_len = [], 0
            current.append(para_with_sep)
            current_len += len(para_with_sep)

    if current and len(chunks) < max_chunks:
        chunks.append("".join(current))

    # Ensure we don't exceed cap
    return chunks[:max_chunks]
