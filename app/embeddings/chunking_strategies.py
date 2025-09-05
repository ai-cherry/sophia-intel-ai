"""
Smart Chunking Strategies for Different Content Types

Advanced content chunking with semantic awareness, overlap management,
and token-aware processing for code, documentation, and conversations.
"""

import ast
import logging
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content for chunking"""

    CODE = "code"
    DOCUMENTATION = "documentation"
    MARKDOWN = "markdown"
    CONVERSATION = "conversation"
    JSON = "json"
    PLAIN_TEXT = "plain_text"


class ChunkingStrategy(Enum):
    """Chunking strategies"""

    FIXED_SIZE = "fixed_size"
    SEMANTIC = "semantic"
    HIERARCHICAL = "hierarchical"
    ADAPTIVE = "adaptive"
    SLIDING_WINDOW = "sliding_window"


@dataclass
class ChunkMetadata:
    """Metadata for a chunk"""

    chunk_id: str
    content_type: ContentType
    strategy: ChunkingStrategy
    start_position: int
    end_position: int
    token_count: int
    overlap_with: List[str] = field(default_factory=list)
    hierarchy_level: Optional[str] = None
    parent_chunk_id: Optional[str] = None
    semantic_boundary: bool = False
    extra_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Chunk:
    """A chunk of content with metadata"""

    content: str
    metadata: ChunkMetadata

    def __len__(self) -> int:
        return len(self.content)

    def token_count(self) -> int:
        """Estimate token count (simple word-based estimation)"""
        return len(self.content.split())


class TokenCounter:
    """Token counting utilities"""

    # Rough token estimation (1 token ≈ 4 characters for English text)
    CHARS_PER_TOKEN = 4

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimate token count for text"""
        # More sophisticated estimation considering code vs natural language
        if TokenCounter.is_code_like(text):
            # Code typically has more tokens per character due to symbols
            return len(text) // 3
        else:
            # Natural language
            return len(text) // TokenCounter.CHARS_PER_TOKEN

    @staticmethod
    def is_code_like(text: str) -> bool:
        """Heuristic to determine if text is code"""
        code_indicators = [
            "def ",
            "class ",
            "import ",
            "from ",
            "return ",
            "if ",
            "for ",
            "while ",
            "{",
            "}",
            "()",
            "=>",
            "->",
            "==",
            "!=",
            "&&",
            "||",
            "#!/",
        ]

        indicator_count = sum(1 for indicator in code_indicators if indicator in text)
        return indicator_count >= 2 or text.strip().startswith(("def ", "class ", "import "))


class BaseChunker(ABC):
    """Base class for content chunkers"""

    def __init__(
        self,
        max_chunk_size: int = 1000,
        overlap_size: int = 100,
        min_chunk_size: int = 50,
        preserve_boundaries: bool = True,
    ):
        """
        Initialize chunker

        Args:
            max_chunk_size: Maximum tokens per chunk
            overlap_size: Overlap tokens between chunks
            min_chunk_size: Minimum tokens per chunk
            preserve_boundaries: Whether to preserve semantic boundaries
        """
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size
        self.min_chunk_size = min_chunk_size
        self.preserve_boundaries = preserve_boundaries
        self._chunk_counter = 0

    @abstractmethod
    def chunk_content(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk content into pieces"""
        pass

    def _generate_chunk_id(self, content_id: str, index: int) -> str:
        """Generate unique chunk ID"""
        return f"{content_id}_chunk_{index:04d}"

    def _create_chunk(
        self,
        content: str,
        content_id: str,
        start_pos: int,
        end_pos: int,
        content_type: ContentType,
        strategy: ChunkingStrategy,
        **kwargs,
    ) -> Chunk:
        """Create a chunk with metadata"""
        chunk_id = self._generate_chunk_id(content_id, self._chunk_counter)
        self._chunk_counter += 1

        metadata = ChunkMetadata(
            chunk_id=chunk_id,
            content_type=content_type,
            strategy=strategy,
            start_position=start_pos,
            end_position=end_pos,
            token_count=TokenCounter.estimate_tokens(content),
            **kwargs,
        )

        return Chunk(content=content, metadata=metadata)

    def _add_overlap(self, chunks: List[Chunk]) -> List[Chunk]:
        """Add overlap between adjacent chunks"""
        if len(chunks) <= 1 or self.overlap_size <= 0:
            return chunks

        overlapped_chunks = []

        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk - no overlap needed at start
                overlapped_chunks.append(chunk)
            else:
                # Get overlap from previous chunk
                prev_chunk = chunks[i - 1]
                prev_words = prev_chunk.content.split()
                current_words = chunk.content.split()

                # Calculate overlap
                overlap_tokens = min(self.overlap_size, len(prev_words), len(current_words))

                if overlap_tokens > 0:
                    # Add overlap from previous chunk to beginning of current
                    overlap_content = " ".join(prev_words[-overlap_tokens:])
                    overlapped_content = overlap_content + "\n" + chunk.content

                    # Update metadata
                    new_metadata = chunk.metadata
                    new_metadata.overlap_with.append(prev_chunk.metadata.chunk_id)
                    new_metadata.token_count = TokenCounter.estimate_tokens(overlapped_content)

                    overlapped_chunk = Chunk(content=overlapped_content, metadata=new_metadata)
                    overlapped_chunks.append(overlapped_chunk)
                else:
                    overlapped_chunks.append(chunk)

        return overlapped_chunks


class CodeChunker(BaseChunker):
    """Specialized chunker for code content"""

    def __init__(self, language: str = "python", **kwargs):
        super().__init__(**kwargs)
        self.language = language.lower()
        self.function_patterns = self._get_function_patterns()
        self.class_patterns = self._get_class_patterns()

    def _get_function_patterns(self) -> Dict[str, re.Pattern]:
        """Get function detection patterns for different languages"""
        patterns = {
            "python": re.compile(r"^(\s*)def\s+(\w+)\s*\([^)]*\)\s*:", re.MULTILINE),
            "javascript": re.compile(
                r"^(\s*)(?:function\s+(\w+)|(\w+)\s*[=:]\s*(?:function|\([^)]*\)\s*=>))",
                re.MULTILINE,
            ),
            "java": re.compile(
                r"^(\s*)(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\([^)]*\)",
                re.MULTILINE,
            ),
            "cpp": re.compile(r"^(\s*)\w+\s+(\w+)\s*\([^)]*\)\s*{?", re.MULTILINE),
            "go": re.compile(r"^(\s*)func\s+(\w+)\s*\([^)]*\)", re.MULTILINE),
        }
        return patterns.get(self.language, patterns["python"])

    def _get_class_patterns(self) -> Dict[str, re.Pattern]:
        """Get class detection patterns for different languages"""
        patterns = {
            "python": re.compile(r"^(\s*)class\s+(\w+)(?:\([^)]*\))?\s*:", re.MULTILINE),
            "javascript": re.compile(r"^(\s*)class\s+(\w+)", re.MULTILINE),
            "java": re.compile(
                r"^(\s*)(?:public|private|protected)?\s*class\s+(\w+)", re.MULTILINE
            ),
            "cpp": re.compile(r"^(\s*)class\s+(\w+)", re.MULTILINE),
            "go": re.compile(r"^(\s*)type\s+(\w+)\s+struct", re.MULTILINE),
        }
        return patterns.get(self.language, patterns["python"])

    def chunk_content(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk code content into logical units"""
        if self.language == "python":
            return self._chunk_python_code(content, content_id)
        else:
            return self._chunk_generic_code(content, content_id)

    def _chunk_python_code(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk Python code using AST analysis"""
        chunks = []

        try:
            tree = ast.parse(content)

            # Extract top-level definitions
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    chunk_content = self._extract_node_content(content, node)
                    if chunk_content and len(chunk_content.strip()) >= self.min_chunk_size:
                        chunk = self._create_chunk(
                            chunk_content,
                            content_id,
                            node.lineno,
                            getattr(node, "end_lineno", node.lineno),
                            ContentType.CODE,
                            ChunkingStrategy.HIERARCHICAL,
                            hierarchy_level=(
                                "function"
                                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                                else "class"
                            ),
                            extra_metadata={
                                "name": node.name,
                                "type": type(node).__name__,
                                "language": self.language,
                            },
                        )
                        chunks.append(chunk)

            # If no large structures found, fall back to line-based chunking
            if not chunks:
                chunks = self._chunk_by_lines(content, content_id)

        except SyntaxError:
            logger.warning(f"Syntax error in {content_id}, falling back to line-based chunking")
            chunks = self._chunk_by_lines(content, content_id)

        return self._add_overlap(chunks)

    def _extract_node_content(self, full_content: str, node: ast.AST) -> str:
        """Extract content for an AST node"""
        lines = full_content.split("\n")
        start_line = node.lineno - 1  # AST is 1-indexed
        end_line = getattr(node, "end_lineno", node.lineno)

        return "\n".join(lines[start_line:end_line])

    def _chunk_generic_code(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk code for non-Python languages"""
        chunks = []
        lines = content.split("\n")

        # Find function and class boundaries
        boundaries = []

        # Find functions
        for match in self.function_patterns.finditer(content):
            line_num = content[: match.start()].count("\n")
            boundaries.append(
                ("function", line_num, match.group(2) if match.lastindex >= 2 else "unknown")
            )

        # Find classes
        for match in self.class_patterns.finditer(content):
            line_num = content[: match.start()].count("\n")
            boundaries.append(
                ("class", line_num, match.group(2) if match.lastindex >= 2 else "unknown")
            )

        boundaries.sort(key=lambda x: x[1])  # Sort by line number

        # Create chunks based on boundaries
        prev_end = 0
        for i, (boundary_type, line_num, name) in enumerate(boundaries):
            # Find end of this boundary
            next_start = boundaries[i + 1][1] if i + 1 < len(boundaries) else len(lines)

            # Extract content
            chunk_lines = lines[line_num:next_start]
            chunk_content = "\n".join(chunk_lines)

            if len(chunk_content.strip()) >= self.min_chunk_size:
                chunk = self._create_chunk(
                    chunk_content,
                    content_id,
                    line_num,
                    next_start - 1,
                    ContentType.CODE,
                    ChunkingStrategy.HIERARCHICAL,
                    hierarchy_level=boundary_type,
                    extra_metadata={"name": name, "type": boundary_type, "language": self.language},
                )
                chunks.append(chunk)

        # If no boundaries found, use line-based chunking
        if not chunks:
            chunks = self._chunk_by_lines(content, content_id)

        return self._add_overlap(chunks)

    def _chunk_by_lines(self, content: str, content_id: str) -> List[Chunk]:
        """Fall back to line-based chunking"""
        chunks = []
        lines = content.split("\n")

        current_chunk_lines = []
        current_tokens = 0
        start_line = 0

        for i, line in enumerate(lines):
            line_tokens = TokenCounter.estimate_tokens(line)

            if current_tokens + line_tokens > self.max_chunk_size and current_chunk_lines:
                # Create chunk
                chunk_content = "\n".join(current_chunk_lines)
                chunk = self._create_chunk(
                    chunk_content,
                    content_id,
                    start_line,
                    i - 1,
                    ContentType.CODE,
                    ChunkingStrategy.FIXED_SIZE,
                    extra_metadata={"language": self.language},
                )
                chunks.append(chunk)

                # Start new chunk
                current_chunk_lines = [line]
                current_tokens = line_tokens
                start_line = i
            else:
                current_chunk_lines.append(line)
                current_tokens += line_tokens

        # Add final chunk
        if current_chunk_lines:
            chunk_content = "\n".join(current_chunk_lines)
            chunk = self._create_chunk(
                chunk_content,
                content_id,
                start_line,
                len(lines) - 1,
                ContentType.CODE,
                ChunkingStrategy.FIXED_SIZE,
                extra_metadata={"language": self.language},
            )
            chunks.append(chunk)

        return chunks

    def create_hierarchical_chunks(self, content: str, content_id: str) -> Dict[str, List[Chunk]]:
        """Create chunks at multiple hierarchy levels"""
        hierarchical_chunks = {}

        if self.language == "python":
            try:
                tree = ast.parse(content)

                # File level
                file_chunk = self._create_chunk(
                    content,
                    content_id,
                    0,
                    len(content.split("\n")) - 1,
                    ContentType.CODE,
                    ChunkingStrategy.HIERARCHICAL,
                    hierarchy_level="file",
                    extra_metadata={"language": self.language},
                )
                hierarchical_chunks["file"] = [file_chunk]

                # Class level
                class_chunks = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        chunk_content = self._extract_node_content(content, node)
                        class_chunk = self._create_chunk(
                            chunk_content,
                            content_id,
                            node.lineno,
                            getattr(node, "end_lineno", node.lineno),
                            ContentType.CODE,
                            ChunkingStrategy.HIERARCHICAL,
                            hierarchy_level="class",
                            extra_metadata={
                                "name": node.name,
                                "type": "ClassDef",
                                "language": self.language,
                            },
                        )
                        class_chunks.append(class_chunk)

                hierarchical_chunks["class"] = class_chunks

                # Method/Function level
                method_chunks = []
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        chunk_content = self._extract_node_content(content, node)
                        method_chunk = self._create_chunk(
                            chunk_content,
                            content_id,
                            node.lineno,
                            getattr(node, "end_lineno", node.lineno),
                            ContentType.CODE,
                            ChunkingStrategy.HIERARCHICAL,
                            hierarchy_level="method",
                            extra_metadata={
                                "name": node.name,
                                "type": type(node).__name__,
                                "language": self.language,
                            },
                        )
                        method_chunks.append(method_chunk)

                hierarchical_chunks["method"] = method_chunks

                # Block level (logical blocks within methods)
                block_chunks = self._extract_code_blocks(content, content_id)
                hierarchical_chunks["block"] = block_chunks

            except SyntaxError:
                # Fall back to simple chunking
                chunks = self.chunk_content(content, content_id)
                hierarchical_chunks = {"block": chunks}
        else:
            # For non-Python languages, use pattern-based approach
            chunks = self.chunk_content(content, content_id)
            hierarchical_chunks = {"block": chunks}

        return hierarchical_chunks

    def _extract_code_blocks(self, content: str, content_id: str) -> List[Chunk]:
        """Extract logical code blocks (if/for/try blocks, etc.)"""
        blocks = []
        lines = content.split("\n")

        current_block = []
        current_indent = 0
        block_start = 0

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                if current_block:
                    current_block.append(line)
                continue

            # Calculate indentation
            indent = len(line) - len(line.lstrip())

            # Detect block starts
            is_block_start = any(
                stripped.startswith(keyword)
                for keyword in [
                    "def ",
                    "class ",
                    "if ",
                    "for ",
                    "while ",
                    "try:",
                    "with ",
                    "elif ",
                    "else:",
                ]
            )

            if is_block_start or (current_block and indent <= current_indent and current_block):
                # End current block
                if current_block and len("\n".join(current_block).strip()) >= self.min_chunk_size:
                    block_content = "\n".join(current_block)
                    block = self._create_chunk(
                        block_content,
                        content_id,
                        block_start,
                        i - 1,
                        ContentType.CODE,
                        ChunkingStrategy.SEMANTIC,
                        hierarchy_level="block",
                        semantic_boundary=True,
                        extra_metadata={"language": self.language},
                    )
                    blocks.append(block)

                # Start new block
                current_block = [line]
                current_indent = indent
                block_start = i
            else:
                current_block.append(line)

        # Add final block
        if current_block and len("\n".join(current_block).strip()) >= self.min_chunk_size:
            block_content = "\n".join(current_block)
            block = self._create_chunk(
                block_content,
                content_id,
                block_start,
                len(lines) - 1,
                ContentType.CODE,
                ChunkingStrategy.SEMANTIC,
                hierarchy_level="block",
                semantic_boundary=True,
                extra_metadata={"language": self.language},
            )
            blocks.append(block)

        return blocks


class DocumentationChunker(BaseChunker):
    """Specialized chunker for documentation and markdown content"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.heading_pattern = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)
        self.paragraph_separator = re.compile(r"\n\s*\n")

    def chunk_content(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk documentation content by semantic sections"""
        if self._is_markdown(content):
            return self._chunk_markdown(content, content_id)
        else:
            return self._chunk_text_document(content, content_id)

    def _is_markdown(self, content: str) -> bool:
        """Detect if content is markdown"""
        markdown_indicators = [
            r"^#{1,6}\s",  # Headers
            r"^\*\s",  # Bullet points
            r"^\d+\.\s",  # Numbered lists
            r"```",  # Code blocks
            r"\[.*\]\(.*\)",  # Links
        ]

        for pattern in markdown_indicators:
            if re.search(pattern, content, re.MULTILINE):
                return True
        return False

    def _chunk_markdown(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk markdown content by headers and sections"""
        chunks = []

        # Find all headings
        headings = list(self.heading_pattern.finditer(content))

        if not headings:
            # No headings found, chunk by paragraphs
            return self._chunk_by_paragraphs(content, content_id)

        # Create chunks based on sections
        for i, heading_match in enumerate(headings):
            section_start = heading_match.start()

            # Find end of section (next heading at same or higher level)
            heading_level = len(heading_match.group(1))
            section_end = len(content)

            for j in range(i + 1, len(headings)):
                next_heading = headings[j]
                next_level = len(next_heading.group(1))

                if next_level <= heading_level:
                    section_end = next_heading.start()
                    break

            # Extract section content
            section_content = content[section_start:section_end].strip()

            if len(section_content) >= self.min_chunk_size:
                # Calculate line numbers
                start_line = content[:section_start].count("\n")
                end_line = content[:section_end].count("\n")

                chunk = self._create_chunk(
                    section_content,
                    content_id,
                    start_line,
                    end_line,
                    ContentType.MARKDOWN,
                    ChunkingStrategy.SEMANTIC,
                    hierarchy_level=f"h{heading_level}",
                    semantic_boundary=True,
                    extra_metadata={
                        "heading": heading_match.group(2).strip(),
                        "heading_level": heading_level,
                    },
                )
                chunks.append(chunk)

            # If section is too large, subdivide it
            elif TokenCounter.estimate_tokens(section_content) > self.max_chunk_size:
                sub_chunks = self._subdivide_large_section(
                    section_content, content_id, section_start
                )
                chunks.extend(sub_chunks)

        return self._add_overlap(chunks)

    def _chunk_by_paragraphs(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk content by paragraphs"""
        chunks = []
        paragraphs = self.paragraph_separator.split(content)

        current_chunk_parts = []
        current_tokens = 0
        start_pos = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            para_tokens = TokenCounter.estimate_tokens(paragraph)

            if current_tokens + para_tokens > self.max_chunk_size and current_chunk_parts:
                # Create chunk from current parts
                chunk_content = "\n\n".join(current_chunk_parts)
                chunk = self._create_chunk(
                    chunk_content,
                    content_id,
                    start_pos,
                    start_pos + len(chunk_content),
                    ContentType.DOCUMENTATION,
                    ChunkingStrategy.SEMANTIC,
                    semantic_boundary=True,
                )
                chunks.append(chunk)

                # Start new chunk
                current_chunk_parts = [paragraph]
                current_tokens = para_tokens
                start_pos += len(chunk_content) + 2  # +2 for paragraph separator
            else:
                current_chunk_parts.append(paragraph)
                current_tokens += para_tokens

        # Add final chunk
        if current_chunk_parts:
            chunk_content = "\n\n".join(current_chunk_parts)
            chunk = self._create_chunk(
                chunk_content,
                content_id,
                start_pos,
                start_pos + len(chunk_content),
                ContentType.DOCUMENTATION,
                ChunkingStrategy.SEMANTIC,
                semantic_boundary=True,
            )
            chunks.append(chunk)

        return chunks

    def _chunk_text_document(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk plain text document"""
        # Simple sentence-aware chunking
        sentences = self._split_into_sentences(content)

        chunks = []
        current_chunk_sentences = []
        current_tokens = 0

        for sentence in sentences:
            sentence_tokens = TokenCounter.estimate_tokens(sentence)

            if current_tokens + sentence_tokens > self.max_chunk_size and current_chunk_sentences:
                # Create chunk
                chunk_content = " ".join(current_chunk_sentences)
                chunk = self._create_chunk(
                    chunk_content,
                    content_id,
                    0,
                    len(chunk_content),
                    ContentType.PLAIN_TEXT,
                    ChunkingStrategy.SEMANTIC,
                    semantic_boundary=True,
                )
                chunks.append(chunk)

                # Start new chunk
                current_chunk_sentences = [sentence]
                current_tokens = sentence_tokens
            else:
                current_chunk_sentences.append(sentence)
                current_tokens += sentence_tokens

        # Add final chunk
        if current_chunk_sentences:
            chunk_content = " ".join(current_chunk_sentences)
            chunk = self._create_chunk(
                chunk_content,
                content_id,
                0,
                len(chunk_content),
                ContentType.PLAIN_TEXT,
                ChunkingStrategy.SEMANTIC,
                semantic_boundary=True,
            )
            chunks.append(chunk)

        return chunks

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting (could be improved with nltk or spacy)
        sentence_endings = re.compile(r"[.!?]+\s+")
        sentences = sentence_endings.split(text)

        # Clean up sentences
        return [s.strip() for s in sentences if s.strip()]

    def _subdivide_large_section(
        self, section_content: str, content_id: str, base_position: int
    ) -> List[Chunk]:
        """Subdivide a large section into smaller chunks"""
        # Use paragraph-based subdivision
        paragraphs = self.paragraph_separator.split(section_content)

        chunks = []
        current_chunk_parts = []
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            para_tokens = TokenCounter.estimate_tokens(paragraph)

            if current_tokens + para_tokens > self.max_chunk_size and current_chunk_parts:
                chunk_content = "\n\n".join(current_chunk_parts)
                chunk = self._create_chunk(
                    chunk_content,
                    content_id,
                    base_position,
                    base_position + len(chunk_content),
                    ContentType.MARKDOWN,
                    ChunkingStrategy.ADAPTIVE,
                    semantic_boundary=True,
                )
                chunks.append(chunk)

                current_chunk_parts = [paragraph]
                current_tokens = para_tokens
                base_position += len(chunk_content) + 2
            else:
                current_chunk_parts.append(paragraph)
                current_tokens += para_tokens

        # Add final chunk
        if current_chunk_parts:
            chunk_content = "\n\n".join(current_chunk_parts)
            chunk = self._create_chunk(
                chunk_content,
                content_id,
                base_position,
                base_position + len(chunk_content),
                ContentType.MARKDOWN,
                ChunkingStrategy.ADAPTIVE,
                semantic_boundary=True,
            )
            chunks.append(chunk)

        return chunks


class ConversationChunker(BaseChunker):
    """Specialized chunker for conversation and chat data"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.message_pattern = re.compile(
            r"^(User|Assistant|System|Human|AI):\s*(.*)$", re.MULTILINE | re.IGNORECASE
        )
        self.turn_boundary = re.compile(r"\n(?=(?:User|Assistant|System|Human|AI):)", re.IGNORECASE)

    def chunk_content(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk conversation content by message exchanges"""
        # Detect conversation format
        if self.message_pattern.search(content):
            return self._chunk_structured_conversation(content, content_id)
        else:
            return self._chunk_unstructured_conversation(content, content_id)

    def _chunk_structured_conversation(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk structured conversation (User: ... Assistant: ...)"""
        chunks = []

        # Split by conversation turns
        turns = self.turn_boundary.split(content)

        current_exchange = []
        current_tokens = 0
        exchange_count = 0

        for turn in turns:
            turn = turn.strip()
            if not turn:
                continue

            turn_tokens = TokenCounter.estimate_tokens(turn)

            # Check if adding this turn would exceed max size
            if current_tokens + turn_tokens > self.max_chunk_size and current_exchange:
                # Create chunk from current exchange
                exchange_content = "\n\n".join(current_exchange)
                chunk = self._create_chunk(
                    exchange_content,
                    content_id,
                    0,
                    len(exchange_content),
                    ContentType.CONVERSATION,
                    ChunkingStrategy.SEMANTIC,
                    hierarchy_level="exchange",
                    semantic_boundary=True,
                    extra_metadata={
                        "exchange_id": exchange_count,
                        "turn_count": len(current_exchange),
                    },
                )
                chunks.append(chunk)

                # Start new exchange
                current_exchange = [turn]
                current_tokens = turn_tokens
                exchange_count += 1
            else:
                current_exchange.append(turn)
                current_tokens += turn_tokens

        # Add final exchange
        if current_exchange:
            exchange_content = "\n\n".join(current_exchange)
            chunk = self._create_chunk(
                exchange_content,
                content_id,
                0,
                len(exchange_content),
                ContentType.CONVERSATION,
                ChunkingStrategy.SEMANTIC,
                hierarchy_level="exchange",
                semantic_boundary=True,
                extra_metadata={"exchange_id": exchange_count, "turn_count": len(current_exchange)},
            )
            chunks.append(chunk)

        return chunks

    def _chunk_unstructured_conversation(self, content: str, content_id: str) -> List[Chunk]:
        """Chunk unstructured conversation content"""
        # Fall back to paragraph-based chunking with conversation awareness
        paragraphs = re.split(r"\n\s*\n", content)

        chunks = []
        current_chunk_parts = []
        current_tokens = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            para_tokens = TokenCounter.estimate_tokens(paragraph)

            if current_tokens + para_tokens > self.max_chunk_size and current_chunk_parts:
                chunk_content = "\n\n".join(current_chunk_parts)
                chunk = self._create_chunk(
                    chunk_content,
                    content_id,
                    0,
                    len(chunk_content),
                    ContentType.CONVERSATION,
                    ChunkingStrategy.ADAPTIVE,
                    semantic_boundary=True,
                )
                chunks.append(chunk)

                current_chunk_parts = [paragraph]
                current_tokens = para_tokens
            else:
                current_chunk_parts.append(paragraph)
                current_tokens += para_tokens

        # Add final chunk
        if current_chunk_parts:
            chunk_content = "\n\n".join(current_chunk_parts)
            chunk = self._create_chunk(
                chunk_content,
                content_id,
                0,
                len(chunk_content),
                ContentType.CONVERSATION,
                ChunkingStrategy.ADAPTIVE,
                semantic_boundary=True,
            )
            chunks.append(chunk)

        return chunks


class AdaptiveChunker:
    """Adaptive chunker that selects the best strategy based on content analysis"""

    def __init__(self, max_chunk_size: int = 1000, overlap_size: int = 100):
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

        # Initialize specialized chunkers
        self.code_chunker = CodeChunker(max_chunk_size=max_chunk_size, overlap_size=overlap_size)
        self.doc_chunker = DocumentationChunker(
            max_chunk_size=max_chunk_size, overlap_size=overlap_size
        )
        self.conversation_chunker = ConversationChunker(
            max_chunk_size=max_chunk_size, overlap_size=overlap_size
        )

    def chunk_content(
        self, content: str, content_id: str, content_type: Optional[ContentType] = None
    ) -> List[Chunk]:
        """Adaptively chunk content based on detected type"""

        # Detect content type if not provided
        if content_type is None:
            content_type = self._detect_content_type(content)

        # Select appropriate chunker
        if content_type == ContentType.CODE:
            language = self._detect_programming_language(content)
            self.code_chunker.language = language
            return self.code_chunker.chunk_content(content, content_id)

        elif content_type in [ContentType.DOCUMENTATION, ContentType.MARKDOWN]:
            return self.doc_chunker.chunk_content(content, content_id)

        elif content_type == ContentType.CONVERSATION:
            return self.conversation_chunker.chunk_content(content, content_id)

        else:
            # Default to documentation chunker for plain text
            return self.doc_chunker._chunk_text_document(content, content_id)

    def _detect_content_type(self, content: str) -> ContentType:
        """Detect the type of content"""
        content_lower = content.lower()

        # Check for code indicators
        code_patterns = [
            r"\bdef\s+\w+\s*\(",  # Python functions
            r"\bclass\s+\w+",  # Classes
            r"\bimport\s+\w+",  # Imports
            r"\{[\s\S]*\}",  # Code blocks
            r"function\s+\w+",  # JavaScript functions
            r"public\s+class",  # Java classes
        ]

        code_score = sum(1 for pattern in code_patterns if re.search(pattern, content))

        # Check for conversation indicators
        conversation_patterns = [
            r"^(User|Human|Assistant|AI):\s",
            r"Q:\s",
            r"A:\s",
        ]

        conversation_score = sum(
            1
            for pattern in conversation_patterns
            if re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
        )

        # Check for markdown indicators
        markdown_patterns = [
            r"^#{1,6}\s",  # Headers
            r"^\*\s",  # Bullet points
            r"```",  # Code blocks
            r"\[.*\]\(.*\)",  # Links
        ]

        markdown_score = sum(
            1 for pattern in markdown_patterns if re.search(pattern, content, re.MULTILINE)
        )

        # Determine content type based on scores
        if code_score >= 2:
            return ContentType.CODE
        elif conversation_score >= 1:
            return ContentType.CONVERSATION
        elif markdown_score >= 2:
            return ContentType.MARKDOWN
        else:
            return ContentType.PLAIN_TEXT

    def _detect_programming_language(self, content: str) -> str:
        """Detect programming language from content"""
        language_indicators = {
            "python": [r"\bdef\s+\w+", r"\bimport\s+\w+", r"\bclass\s+\w+:", r"#\s*.*"],
            "javascript": [r"\bfunction\s+\w+", r"\bvar\s+\w+", r"\bconst\s+\w+", r"//.*"],
            "java": [r"\bpublic\s+class", r"\bpublic\s+static\s+void", r"import\s+\w+\.\*;"],
            "cpp": [r"#include\s*<", r"\bint\s+main\s*\(", r"std::"],
            "go": [r"\bfunc\s+\w+", r"\bpackage\s+\w+", r'\bimport\s+"'],
        }

        scores = {}
        for lang, patterns in language_indicators.items():
            score = sum(1 for pattern in patterns if re.search(pattern, content))
            if score > 0:
                scores[lang] = score

        if scores:
            return max(scores.items(), key=lambda x: x[1])[0]
        else:
            return "python"  # Default

    def get_chunking_stats(self, chunks: List[Chunk]) -> Dict[str, Any]:
        """Get statistics about the chunking results"""
        if not chunks:
            return {}

        total_chunks = len(chunks)
        total_tokens = sum(chunk.metadata.token_count for chunk in chunks)
        avg_tokens = total_tokens / total_chunks if total_chunks > 0 else 0

        content_types = {}
        strategies = {}
        hierarchy_levels = {}

        for chunk in chunks:
            # Count content types
            ct = chunk.metadata.content_type.value
            content_types[ct] = content_types.get(ct, 0) + 1

            # Count strategies
            st = chunk.metadata.strategy.value
            strategies[st] = strategies.get(st, 0) + 1

            # Count hierarchy levels
            if chunk.metadata.hierarchy_level:
                hl = chunk.metadata.hierarchy_level
                hierarchy_levels[hl] = hierarchy_levels.get(hl, 0) + 1

        return {
            "total_chunks": total_chunks,
            "total_tokens": total_tokens,
            "average_tokens_per_chunk": avg_tokens,
            "content_types": content_types,
            "strategies": strategies,
            "hierarchy_levels": hierarchy_levels,
            "semantic_boundaries": sum(1 for c in chunks if c.metadata.semantic_boundary),
            "overlapped_chunks": sum(1 for c in chunks if c.metadata.overlap_with),
        }
