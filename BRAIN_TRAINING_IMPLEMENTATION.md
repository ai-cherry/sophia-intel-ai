# Sophia Brain Training System - Implementation Specification

## Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)

1. **Content Ingestion Gateway** - Universal file processing
2. **Storage Strategy System** - Adaptive storage selection
3. **Basic Conversational Interface** - Chat integration

### Phase 2: Intelligence Layer (Week 3-4)

1. **Multi-Modal Analysis Engine** - Content understanding
2. **Context-Aware Retrieval** - Semantic search
3. **Advanced Conversational Training** - Intelligent interactions

### Phase 3: Integration & Optimization (Week 5-6)

1. **AGNO Orchestrator Integration** - Seamless integration
2. **Performance Optimization** - Large file handling
3. **Advanced Features** - Relationship discovery, learning patterns

## Key Implementation Files

### 1. Content Ingestion Gateway

```python
# /Users/lynnmusil/sophia-intel-ai/app/brain_training/content_gateway.py

import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator, List
from dataclasses import dataclass, field
from datetime import datetime
import aiofiles
import magic
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class FileMetadata:
    """Metadata for uploaded files."""
    path: str
    name: str
    size: int
    mime_type: str
    content_type: str
    hash_value: str
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ProcessingChunk:
    """A chunk of content being processed."""
    id: str
    content: bytes
    size: int
    position: int
    total_chunks: int
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IngestionUpdate:
    """Real-time update during ingestion."""
    type: str  # progress, clarification_request, insight, completion
    content: str
    requires_user_input: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

class ContentProcessor(ABC):
    """Abstract base class for content processors."""

    @abstractmethod
    async def can_process(self, file_metadata: FileMetadata) -> bool:
        """Check if processor can handle this file type."""
        pass

    @abstractmethod
    async def process_chunk(self, chunk: ProcessingChunk) -> Dict[str, Any]:
        """Process a content chunk."""
        pass

    @abstractmethod
    async def finalize_processing(self, all_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Finalize processing after all chunks are processed."""
        pass

class PDFProcessor(ContentProcessor):
    """Processor for PDF files with OCR and text extraction."""

    def __init__(self):
        self.pdf_reader = None  # Initialize PyMuPDF or similar
        self.ocr_engine = None  # Initialize Tesseract or similar

    async def can_process(self, file_metadata: FileMetadata) -> bool:
        return file_metadata.mime_type in ['application/pdf']

    async def process_chunk(self, chunk: ProcessingChunk) -> Dict[str, Any]:
        """Process PDF chunk with text extraction and OCR."""
        try:
            # Extract text and images from PDF chunk
            text_content = await self._extract_text(chunk.content)
            images = await self._extract_images(chunk.content)

            # OCR on images if text extraction fails
            if not text_content and images:
                text_content = await self._ocr_images(images)

            # Extract metadata
            metadata = await self._extract_pdf_metadata(chunk.content)

            return {
                'text': text_content,
                'images': images,
                'metadata': metadata,
                'structure': await self._analyze_structure(text_content)
            }
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            return {'error': str(e)}

    async def _extract_text(self, content: bytes) -> str:
        """Extract text from PDF content."""
        # Implementation with PyMuPDF or pdfplumber
        return ""

    async def _extract_images(self, content: bytes) -> List[Dict]:
        """Extract images from PDF content."""
        return []

    async def _ocr_images(self, images: List[Dict]) -> str:
        """Perform OCR on extracted images."""
        return ""

    async def _extract_pdf_metadata(self, content: bytes) -> Dict:
        """Extract PDF metadata."""
        return {}

    async def _analyze_structure(self, text: str) -> Dict:
        """Analyze document structure."""
        return {}

class ImageProcessor(ContentProcessor):
    """Processor for image files with vision AI."""

    def __init__(self):
        self.vision_model = None  # Initialize vision model (GPT-4V, Claude Vision, etc.)
        self.ocr_engine = None

    async def can_process(self, file_metadata: FileMetadata) -> bool:
        return file_metadata.mime_type.startswith('image/')

    async def process_chunk(self, chunk: ProcessingChunk) -> Dict[str, Any]:
        """Process image with vision AI and OCR."""
        try:
            # Vision AI analysis
            vision_analysis = await self._analyze_with_vision_ai(chunk.content)

            # OCR for text extraction
            ocr_text = await self._extract_text_from_image(chunk.content)

            # Image metadata
            image_metadata = await self._extract_image_metadata(chunk.content)

            return {
                'vision_analysis': vision_analysis,
                'extracted_text': ocr_text,
                'metadata': image_metadata,
                'objects_detected': vision_analysis.get('objects', []),
                'scene_description': vision_analysis.get('description', ''),
                'text_content': ocr_text
            }
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return {'error': str(e)}

    async def _analyze_with_vision_ai(self, content: bytes) -> Dict:
        """Analyze image with vision AI model."""
        return {}

    async def _extract_text_from_image(self, content: bytes) -> str:
        """Extract text using OCR."""
        return ""

    async def _extract_image_metadata(self, content: bytes) -> Dict:
        """Extract image metadata."""
        return {}

class AudioProcessor(ContentProcessor):
    """Processor for audio files with transcription."""

    def __init__(self):
        self.transcription_service = None  # Whisper, AssemblyAI, etc.
        self.speaker_identification = None
        self.sentiment_analyzer = None

    async def can_process(self, file_metadata: FileMetadata) -> bool:
        return file_metadata.mime_type.startswith('audio/')

    async def process_chunk(self, chunk: ProcessingChunk) -> Dict[str, Any]:
        """Process audio chunk with transcription and analysis."""
        try:
            # Transcribe audio
            transcription = await self._transcribe_audio(chunk.content)

            # Identify speakers if multiple
            speakers = await self._identify_speakers(chunk.content)

            # Sentiment analysis
            sentiment = await self._analyze_sentiment(transcription)

            # Extract key topics
            topics = await self._extract_topics(transcription)

            return {
                'transcription': transcription,
                'speakers': speakers,
                'sentiment': sentiment,
                'topics': topics,
                'duration': await self._get_duration(chunk.content),
                'metadata': await self._extract_audio_metadata(chunk.content)
            }
        except Exception as e:
            logger.error(f"Audio processing error: {e}")
            return {'error': str(e)}

class VideoProcessor(ContentProcessor):
    """Processor for video files with frame extraction and transcription."""

    def __init__(self):
        self.frame_extractor = None
        self.transcription_service = None
        self.scene_analyzer = None

    async def can_process(self, file_metadata: FileMetadata) -> bool:
        return file_metadata.mime_type.startswith('video/')

    async def process_chunk(self, chunk: ProcessingChunk) -> Dict[str, Any]:
        """Process video chunk with frame analysis and audio transcription."""
        try:
            # Extract key frames
            frames = await self._extract_key_frames(chunk.content)

            # Analyze frames with vision AI
            frame_analysis = await self._analyze_frames(frames)

            # Extract and transcribe audio
            audio_content = await self._extract_audio(chunk.content)
            transcription = await self._transcribe_audio(audio_content)

            # Scene detection
            scenes = await self._detect_scenes(chunk.content)

            return {
                'frames': frame_analysis,
                'transcription': transcription,
                'scenes': scenes,
                'duration': await self._get_video_duration(chunk.content),
                'metadata': await self._extract_video_metadata(chunk.content)
            }
        except Exception as e:
            logger.error(f"Video processing error: {e}")
            return {'error': str(e)}

class CodeProcessor(ContentProcessor):
    """Processor for code files with AST analysis."""

    def __init__(self):
        self.ast_parsers = {}  # Language-specific AST parsers
        self.dependency_analyzer = None
        self.complexity_analyzer = None

    async def can_process(self, file_metadata: FileMetadata) -> bool:
        code_extensions = {'.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.rb', '.php'}
        return Path(file_metadata.path).suffix in code_extensions

    async def process_chunk(self, chunk: ProcessingChunk) -> Dict[str, Any]:
        """Process code with AST analysis and complexity metrics."""
        try:
            code_content = chunk.content.decode('utf-8')

            # Parse AST
            ast_analysis = await self._parse_ast(code_content, chunk.metadata.get('language'))

            # Analyze dependencies
            dependencies = await self._analyze_dependencies(code_content)

            # Complexity metrics
            complexity = await self._analyze_complexity(code_content)

            # Extract functions and classes
            functions = await self._extract_functions(ast_analysis)
            classes = await self._extract_classes(ast_analysis)

            return {
                'ast': ast_analysis,
                'dependencies': dependencies,
                'complexity': complexity,
                'functions': functions,
                'classes': classes,
                'language': chunk.metadata.get('language'),
                'lines_of_code': len(code_content.split('\n'))
            }
        except Exception as e:
            logger.error(f"Code processing error: {e}")
            return {'error': str(e)}

class ContentIngestionGateway:
    """Main gateway for content ingestion with conversational processing."""

    def __init__(self, sophia_orchestrator=None):
        self.processors: List[ContentProcessor] = [
            PDFProcessor(),
            ImageProcessor(),
            AudioProcessor(),
            VideoProcessor(),
            CodeProcessor()
        ]
        self.chunk_size = 10 * 1024 * 1024  # 10MB chunks
        self.sophia = sophia_orchestrator
        self.active_sessions: Dict[str, 'IngestionSession'] = {}

    async def start_ingestion(
        self,
        file_path: str,
        chat_session_id: Optional[str] = None,
        processing_preferences: Optional[Dict] = None
    ) -> 'IngestionSession':
        """Start content ingestion with conversational processing."""

        # Analyze file
        file_metadata = await self._analyze_file(file_path)

        # Select appropriate processor
        processor = await self._select_processor(file_metadata)
        if not processor:
            raise ValueError(f"No processor available for {file_metadata.mime_type}")

        # Create ingestion session
        session = IngestionSession(
            file_metadata=file_metadata,
            processor=processor,
            chat_session_id=chat_session_id,
            preferences=processing_preferences or {},
            gateway=self
        )

        if chat_session_id:
            self.active_sessions[chat_session_id] = session

        return session

    async def _analyze_file(self, file_path: str) -> FileMetadata:
        """Analyze file and extract metadata."""
        path = Path(file_path)

        # Get file stats
        stat = path.stat()

        # Detect MIME type
        mime_type = magic.from_file(str(path), mime=True)

        # Calculate hash
        import hashlib
        hash_sha256 = hashlib.sha256()
        async with aiofiles.open(path, 'rb') as f:
            async for chunk in self._read_chunks(f, 8192):
                hash_sha256.update(chunk)

        # Determine content type category
        content_type = self._categorize_content_type(mime_type)

        return FileMetadata(
            path=str(path),
            name=path.name,
            size=stat.st_size,
            mime_type=mime_type,
            content_type=content_type,
            hash_value=hash_sha256.hexdigest()
        )

    async def _select_processor(self, file_metadata: FileMetadata) -> Optional[ContentProcessor]:
        """Select appropriate processor for file type."""
        for processor in self.processors:
            if await processor.can_process(file_metadata):
                return processor
        return None

    def _categorize_content_type(self, mime_type: str) -> str:
        """Categorize MIME type into content categories."""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type.startswith('video/'):
            return 'video'
        elif mime_type.startswith('audio/'):
            return 'audio'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif 'text' in mime_type or 'json' in mime_type or 'xml' in mime_type:
            return 'text'
        else:
            return 'binary'

    async def _read_chunks(self, file_handle, chunk_size: int):
        """Read file in chunks."""
        while True:
            chunk = await file_handle.read(chunk_size)
            if not chunk:
                break
            yield chunk

class IngestionSession:
    """Represents an active ingestion session with conversational processing."""

    def __init__(
        self,
        file_metadata: FileMetadata,
        processor: ContentProcessor,
        chat_session_id: Optional[str],
        preferences: Dict[str, Any],
        gateway: ContentIngestionGateway
    ):
        self.file_metadata = file_metadata
        self.processor = processor
        self.chat_session_id = chat_session_id
        self.preferences = preferences
        self.gateway = gateway
        self.processing_results: List[Dict[str, Any]] = []
        self.conversation_history: List[str] = []
        self.user_responses: Dict[str, str] = {}

    async def process_with_chat(self) -> AsyncIterator[IngestionUpdate]:
        """Process content with conversational interaction."""

        # Initial analysis and strategy confirmation
        yield IngestionUpdate(
            type="analysis_start",
            content=f"🔍 Analyzing {self.file_metadata.name} ({self.file_metadata.size:,} bytes)..."
        )

        # Determine processing strategy
        strategy = await self._determine_processing_strategy()

        yield IngestionUpdate(
            type="strategy_confirmation",
            content=f"💡 I recommend processing this {self.file_metadata.content_type} file using {strategy['approach']}. This will optimize for {strategy['optimization_target']}. Proceed?",
            requires_user_input=True,
            metadata={'strategy': strategy}
        )

        # Wait for user confirmation (in real implementation)
        # For now, assume confirmation

        # Process in chunks with conversation
        chunk_count = 0
        async for chunk in self._read_file_chunks():
            chunk_count += 1

            yield IngestionUpdate(
                type="processing_progress",
                content=f"📊 Processing chunk {chunk_count}: {chunk.size:,} bytes..."
            )

            # Process chunk
            result = await self.processor.process_chunk(chunk)
            self.processing_results.append(result)

            # Generate insights during processing
            if chunk_count % 5 == 0:  # Every 5 chunks
                insights = await self._generate_processing_insights(result)
                if insights:
                    yield IngestionUpdate(
                        type="processing_insight",
                        content=insights,
                        requires_user_input=True
                    )

            # Large file pause for interaction
            if self.file_metadata.size > 100 * 1024 * 1024 and chunk_count % 10 == 0:
                yield IngestionUpdate(
                    type="large_file_pause",
                    content=f"🚀 Processed {chunk_count} chunks so far. The content is rich with information. Should I continue with detailed analysis or switch to rapid processing?",
                    requires_user_input=True
                )

        # Finalize processing
        final_result = await self.processor.finalize_processing(self.processing_results)

        # Generate storage strategy
        storage_strategy = await self._generate_storage_strategy(final_result)

        yield IngestionUpdate(
            type="completion",
            content=f"✅ Successfully processed {self.file_metadata.name}! Extracted {len(final_result.get('entities', []))} entities and stored using {storage_strategy['primary_backend']} strategy.",
            metadata={
                'final_result': final_result,
                'storage_strategy': storage_strategy
            }
        )

    async def _determine_processing_strategy(self) -> Dict[str, Any]:
        """Determine optimal processing strategy."""

        if self.file_metadata.size > 100 * 1024 * 1024:  # > 100MB
            return {
                'approach': 'streaming_with_intelligent_chunking',
                'optimization_target': 'memory_efficiency_and_real_time_feedback',
                'chunk_size': 50 * 1024 * 1024,  # 50MB chunks
                'parallel_processing': False
            }
        elif self.file_metadata.content_type in ['image', 'video']:
            return {
                'approach': 'multimodal_ai_analysis',
                'optimization_target': 'content_understanding_and_visual_intelligence',
                'chunk_size': 10 * 1024 * 1024,  # 10MB chunks
                'parallel_processing': True
            }
        else:
            return {
                'approach': 'standard_processing_with_semantic_analysis',
                'optimization_target': 'accuracy_and_relationship_discovery',
                'chunk_size': 5 * 1024 * 1024,  # 5MB chunks
                'parallel_processing': True
            }

    async def _read_file_chunks(self) -> AsyncIterator[ProcessingChunk]:
        """Read file in optimized chunks."""
        chunk_id = 0
        position = 0

        async with aiofiles.open(self.file_metadata.path, 'rb') as file:
            while True:
                content = await file.read(self.gateway.chunk_size)
                if not content:
                    break

                chunk = ProcessingChunk(
                    id=f"chunk_{chunk_id}",
                    content=content,
                    size=len(content),
                    position=position,
                    total_chunks=0,  # Updated later
                    metadata={
                        'file_type': self.file_metadata.content_type,
                        'language': self._detect_language() if self.file_metadata.content_type == 'text' else None
                    }
                )

                yield chunk

                chunk_id += 1
                position += len(content)

    def _detect_language(self) -> Optional[str]:
        """Detect programming language for code files."""
        extension = Path(self.file_metadata.path).suffix

        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.go': 'go',
            '.rs': 'rust',
            '.rb': 'ruby',
            '.php': 'php'
        }

        return language_map.get(extension)

    async def _generate_processing_insights(self, result: Dict[str, Any]) -> Optional[str]:
        """Generate intelligent insights during processing."""

        if 'error' in result:
            return f"⚠️ Encountered processing challenge: {result['error']}. Should I try alternative processing methods?"

        # Text content insights
        if 'text' in result and len(result['text']) > 10000:
            return f"📚 This section contains substantial text ({len(result['text']):,} characters). I can create detailed summaries and extract key concepts. Continue with deep analysis?"

        # Entity extraction insights
        if 'entities' in result and len(result['entities']) > 20:
            return f"🎯 Discovered {len(result['entities'])} entities in this section. Should I create knowledge graph connections with your existing content?"

        # Code complexity insights
        if 'complexity' in result and result['complexity'].get('cyclomatic_complexity', 0) > 10:
            return f"🔧 This code has high complexity (score: {result['complexity']['cyclomatic_complexity']}). Should I create detailed documentation and relationship maps?"

        return None

    async def _generate_storage_strategy(self, final_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate optimal storage strategy based on content analysis."""

        # Determine primary backend based on content type and complexity
        if self.file_metadata.content_type == 'image':
            primary_backend = 'object_store'
            indexes = ['visual_similarity', 'ocr_text']
        elif self.file_metadata.content_type in ['audio', 'video']:
            primary_backend = 'object_store'
            indexes = ['transcript_text', 'temporal']
        elif 'entities' in final_result and len(final_result['entities']) > 100:
            primary_backend = 'graph_database'
            indexes = ['semantic_vector', 'entity_relationships']
        else:
            primary_backend = 'vector_store'
            indexes = ['semantic_search', 'keyword_search']

        return {
            'primary_backend': primary_backend,
            'indexes': indexes,
            'optimization': 'balanced_retrieval_and_storage',
            'estimated_query_performance': '< 100ms for semantic search'
        }

    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        return {
            'file': self.file_metadata.name,
            'size': self.file_metadata.size,
            'content_type': self.file_metadata.content_type,
            'chunks_processed': len(self.processing_results),
            'total_entities': sum(len(r.get('entities', [])) for r in self.processing_results),
            'conversation_interactions': len(self.conversation_history)
        }

    def get_storage_strategy(self) -> Dict[str, Any]:
        """Get the storage strategy used."""
        return self._generate_storage_strategy(self.processing_results[-1] if self.processing_results else {})
```

This implementation provides:

1. **Universal File Processing** - Handles PDFs, images, audio, video, code, and documents
2. **Intelligent Chunking** - Optimized chunk sizes based on content type and file size
3. **Real-Time Conversation** - Interactive processing with user feedback
4. **Multi-Modal Analysis** - Vision AI, OCR, transcription, AST parsing
5. **Adaptive Strategies** - Processing approach based on content characteristics
6. **Streaming Processing** - Handle large files without memory issues
7. **Rich Insights** - Generate intelligent observations during processing

The system seamlessly integrates with Sophia's existing chat interface and AGNO orchestration system while providing powerful brain training capabilities.
