from __future__ import annotations

from typing import List


def chunk_text(text: str, max_chunk_size: int = 1000, max_chunks: int = 1000) -> List[str]:
    """
    Simple, stable text chunker.
    - Splits by double newlines first to keep paragraphs together.
    - Concatenates lines until the chunk reaches max_chunk_size.
    - Falls back to hard splitting if a single line exceeds the limit.
    - Caps total chunks to max_chunks to avoid runaway memory.

    Note: This is intentionally naive and deterministic; upgrade to a semantic
    splitter later if needed.
    """
    if not text:
        return []

    chunks: List[str] = []
    current: List[str] = []
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
