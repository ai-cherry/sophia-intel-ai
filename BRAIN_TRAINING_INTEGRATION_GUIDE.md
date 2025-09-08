# Sophia Brain Training System - Integration Guide

## Complete System Integration

This guide shows how the brain training system integrates with the existing Sophia AGNO orchestrator and chat interface to create a comprehensive AI learning platform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Sophia Enhanced Platform                      │
├─────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   Chat Interface │    │ Content Upload   │                  │
│  │   (Streamlit)    │◄──►│    Gateway       │                  │
│  └──────────────────┘    └──────────────────┘                  │
│              │                        │                        │
│              ▼                        ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │          Enhanced AGNO Orchestrator                         │ │
│  │  ┌────────────────┐  ┌─────────────────────────────────────┐│ │
│  │  │ Business Teams │  │    Brain Training System            ││ │
│  │  │ • Sales Intel  │  │ • Content Gateway                   ││ │
│  │  │ • Research     │  │ • Conversational Trainer            ││ │
│  │  │ • Client Mgmt  │  │ • Storage Optimizer                 ││ │
│  │  │ • Market Analy │  │ • Retrieval Engine                  ││ │
│  │  └────────────────┘  └─────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────┘ │
│              │                        │                        │
│              ▼                        ▼                        │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Business Memory  │    │ Training Memory  │                  │
│  │    System        │◄──►│    System        │                  │
│  └──────────────────┘    └──────────────────┘                  │
│              │                        │                        │
│              ▼                        ▼                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │              Adaptive Storage Layer                         │ │
│  │ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │ │
│  │ │ Vector DB   │ │  Graph DB   │ │ Object Store│            │ │
│  │ └─────────────┘ └─────────────┘ └─────────────┘            │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Enhanced Orchestrator Integration

```python
# /Users/lynnmusil/sophia-intel-ai/app/orchestrators/sophia_enhanced_orchestrator.py

from app.orchestrators.sophia_agno_orchestrator import SophiaAGNOOrchestrator
from app.brain_training.content_gateway import ContentIngestionGateway
from app.brain_training.conversational_trainer import ConversationalTrainer
from app.brain_training.storage_optimizer import StorageStrategyOptimizer
from app.brain_training.retrieval_engine import ContextAwareRetrievalEngine

class SophiaEnhancedOrchestrator(SophiaAGNOOrchestrator):
    """
    Enhanced Sophia orchestrator with brain training capabilities.

    Maintains all existing AGNO business intelligence while adding
    comprehensive content learning and conversational training.
    """

    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)

        # Initialize brain training components
        self.brain_training_system = BrainTrainingSystem(self)
        self.content_gateway = ContentIngestionGateway(self)
        self.conversational_trainer = ConversationalTrainer(self)
        self.storage_optimizer = StorageStrategyOptimizer()
        self.retrieval_engine = ContextAwareRetrievalEngine()

        # Enhanced capabilities
        self.supported_operations.extend([
            "content_training",
            "file_ingestion",
            "knowledge_retrieval",
            "conversational_learning"
        ])

        logger.info("💎 Sophia Enhanced Orchestrator initialized - Brain training ready!")

    async def process_request(
        self,
        request: str,
        context: Optional[Dict] = None,
        files: Optional[List[str]] = None
    ) -> Union[AGNOBusinessResponse, BrainTrainingResponse]:
        """
        Enhanced request processing supporting both business intelligence
        and brain training operations.
        """

        # Detect request type
        request_type = await self._classify_request_type(request, files)

        if request_type == "content_training":
            return await self._handle_content_training(request, context, files)
        elif request_type == "knowledge_query":
            return await self._handle_knowledge_query(request, context)
        elif request_type == "file_ingestion":
            return await self._handle_file_ingestion(request, context, files)
        else:
            # Standard business intelligence request
            return await self.process_business_request(request, context)

    async def _classify_request_type(
        self,
        request: str,
        files: Optional[List[str]] = None
    ) -> str:
        """Classify request type for appropriate routing."""

        request_lower = request.lower()

        # File ingestion indicators
        if files or any(keyword in request_lower for keyword in [
            "upload", "ingest", "learn from", "analyze this file", "process", "train on"
        ]):
            return "file_ingestion"

        # Knowledge query indicators
        elif any(keyword in request_lower for keyword in [
            "what do you know about", "find", "search", "recall", "remember", "lookup"
        ]):
            return "knowledge_query"

        # Content training indicators
        elif any(keyword in request_lower for keyword in [
            "teach", "learn", "training", "understand", "knowledge"
        ]):
            return "content_training"

        # Default to business intelligence
        else:
            return "business_intelligence"

    async def _handle_file_ingestion(
        self,
        request: str,
        context: Optional[Dict],
        files: List[str]
    ) -> BrainTrainingResponse:
        """Handle file ingestion with conversational processing."""

        responses = []
        session_id = context.get('session_id') if context else f"ingestion-{int(time.time())}"

        for file_path in files:
            try:
                # Start conversational ingestion session
                ingestion_session = await self.content_gateway.start_ingestion(
                    file_path=file_path,
                    chat_session_id=session_id,
                    processing_preferences=context.get('processing_preferences', {})
                )

                # Process with real-time conversation
                ingestion_updates = []
                async for update in ingestion_session.process_with_chat():
                    ingestion_updates.append(update)

                    # Handle user input requirements
                    if update.requires_user_input:
                        # In real implementation, this would pause for user input
                        # For now, we'll use intelligent defaults based on content
                        user_response = await self._generate_intelligent_default_response(
                            update, ingestion_session
                        )

                        if user_response:
                            await self.conversational_trainer.process_user_response(
                                session_id, user_response, update.metadata.get('intent')
                            )

                # Generate training insights
                training_insights = await self._generate_training_insights(
                    ingestion_session, request
                )

                responses.append(BrainTrainingResponse(
                    success=True,
                    content=self.personality.add_personality_flair(
                        f"✨ Successfully learned from {Path(file_path).name}! I've processed the content and can now provide intelligent insights about it."
                    ),
                    file_processed=file_path,
                    processing_summary=ingestion_session.get_summary(),
                    storage_strategy=await ingestion_session.get_storage_strategy(),
                    training_insights=training_insights,
                    conversation_updates=ingestion_updates
                ))

            except Exception as e:
                logger.error(f"File ingestion failed for {file_path}: {e}")
                responses.append(BrainTrainingResponse(
                    success=False,
                    content=f"I encountered challenges processing {Path(file_path).name}: {str(e)}. Let me try a different approach.",
                    error=str(e)
                ))

        # Consolidate responses
        if len(responses) == 1:
            return responses[0]
        else:
            return self._consolidate_training_responses(responses)

    async def _handle_knowledge_query(
        self,
        request: str,
        context: Optional[Dict]
    ) -> BrainTrainingResponse:
        """Handle knowledge retrieval queries."""

        session_id = context.get('session_id') if context else f"query-{int(time.time())}"

        # Create conversation context
        conversation_context = ConversationContext(
            session_id=session_id,
            conversation_history=context.get('chat_history', []),
            processing_state={'query': request, 'stage': 'retrieval'}
        )

        # Perform context-aware retrieval
        retrieval_result = await self.retrieval_engine.retrieve_with_context(
            query=request,
            conversation_context=conversation_context,
            retrieval_preferences=context.get('retrieval_preferences')
        )

        # Generate conversational response
        response_content = await self._generate_knowledge_response(
            retrieval_result, request, conversation_context
        )

        # Add personality flair
        response_content = self.personality.add_personality_flair(response_content)

        return BrainTrainingResponse(
            success=len(retrieval_result.results) > 0,
            content=response_content,
            query_processed=request,
            retrieval_results=retrieval_result.results,
            knowledge_insights=retrieval_result.insights,
            conversation_suggestions=retrieval_result.conversation_suggestions,
            cross_references=retrieval_result.cross_references
        )

    async def _generate_intelligent_default_response(
        self,
        update: IngestionUpdate,
        session: 'IngestionSession'
    ) -> Optional[str]:
        """Generate intelligent default responses for conversational prompts."""

        # Strategy confirmation defaults
        if update.type == "strategy_confirmation":
            # Generally approve recommended strategies
            return "yes, proceed with the recommended approach"

        # Processing insight defaults
        elif update.type == "processing_insight":
            # For complex content, create detailed analysis
            if "complex" in update.content.lower() or "entities" in update.content.lower():
                return "yes, create detailed analysis and knowledge graphs"
            else:
                return "continue with standard processing"

        # Relationship discovery defaults
        elif update.type == "relationship_discovery":
            # Generally create cross-references for better knowledge connectivity
            return "yes, create comprehensive cross-references"

        return None

    async def _generate_training_insights(
        self,
        session: 'IngestionSession',
        original_request: str
    ) -> List[str]:
        """Generate training insights from ingestion session."""

        insights = []

        summary = session.get_summary()

        # Content complexity insights
        if summary['total_entities'] > 20:
            insights.append(
                f"Rich content with {summary['total_entities']} entities discovered - excellent for building comprehensive knowledge graphs."
            )

        # Processing efficiency insights
        if summary['chunks_processed'] > 10:
            insights.append(
                f"Large content processed efficiently in {summary['chunks_processed']} chunks - streaming approach optimized memory usage."
            )

        # Conversation engagement insights
        if summary['conversation_interactions'] > 3:
            insights.append(
                f"Active learning session with {summary['conversation_interactions']} interactions - system adapted to your preferences."
            )

        # Storage optimization insights
        storage_strategy = await session.get_storage_strategy()
        insights.append(
            f"Optimized for {storage_strategy['optimization']} using {storage_strategy['primary_backend']} - estimated query performance: {storage_strategy['estimated_query_performance']}."
        )

        return insights

    async def _generate_knowledge_response(
        self,
        retrieval_result: RetrievalResult,
        original_query: str,
        context: ConversationContext
    ) -> str:
        """Generate comprehensive knowledge response."""

        if not retrieval_result.results:
            return f"I don't have specific knowledge about that topic yet. Would you like to upload relevant content for me to learn from?"

        # Build response
        response_parts = []

        # Primary answer from top results
        top_results = retrieval_result.results[:3]
        response_parts.append("🧠 **What I Know:**")

        for idx, result in enumerate(top_results, 1):
            response_parts.append(f"{idx}. **{result.title}**: {result.summary[:200]}...")

        # Add insights if available
        if retrieval_result.insights:
            response_parts.append("\n💡 **Key Insights:**")
            for insight in retrieval_result.insights[:3]:
                response_parts.append(f"• {insight}")

        # Add cross-references if available
        if retrieval_result.cross_references:
            response_parts.append(f"\n🔗 **Related Topics**: Found connections to {len(retrieval_result.cross_references)} other areas in your knowledge base.")

        # Add conversation suggestions
        if retrieval_result.conversation_suggestions:
            response_parts.append("\n🤔 **What's Next?**")
            for suggestion in retrieval_result.conversation_suggestions[:2]:
                response_parts.append(f"• {suggestion.message}")

        return "\n".join(response_parts)

# Enhanced Chat Interface Integration
class EnhancedChatInterface:
    """Enhanced Streamlit chat interface with brain training capabilities."""

    def __init__(self):
        self.orchestrator = SophiaEnhancedOrchestrator()
        self.file_processor = FileUploadProcessor()

    def render_enhanced_chat(self):
        """Render enhanced chat interface with file upload capabilities."""

        # File upload section
        st.sidebar.subheader("📚 Brain Training")
        uploaded_files = st.sidebar.file_uploader(
            "Upload files for Sophia to learn from:",
            accept_multiple_files=True,
            type=['pdf', 'txt', 'docx', 'png', 'jpg', 'mp3', 'mp4', 'py', 'js', 'csv', 'xlsx']
        )

        # Processing preferences
        with st.sidebar.expander("🎯 Processing Preferences"):
            processing_depth = st.selectbox(
                "Processing Depth",
                ["Balanced", "Quick Overview", "Detailed Analysis", "Maximum Intelligence"]
            )

            interaction_level = st.selectbox(
                "Interaction Level",
                ["Moderate", "Minimal", "Maximum Guidance"]
            )

            storage_optimization = st.selectbox(
                "Storage Priority",
                ["Balanced", "Speed Optimized", "Storage Efficient", "Accuracy Focused"]
            )

        # Handle file uploads
        if uploaded_files:
            self._handle_file_uploads(uploaded_files, {
                'processing_depth': processing_depth.lower().replace(' ', '_'),
                'interaction_level': interaction_level.lower().replace(' ', '_'),
                'storage_optimization': storage_optimization.lower().replace(' ', '_')
            })

        # Enhanced chat input with context awareness
        self._render_contextual_chat()

    def _handle_file_uploads(self, uploaded_files, preferences):
        """Handle uploaded files for brain training."""

        if st.button(f"🧠 Train Sophia on {len(uploaded_files)} files"):

            # Save uploaded files temporarily
            temp_files = []
            for uploaded_file in uploaded_files:
                temp_path = f"/tmp/{uploaded_file.name}"
                with open(temp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                temp_files.append(temp_path)

            # Process files with progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            with st.spinner("🎯 Training Sophia's brain..."):

                # Process files
                response = asyncio.run(self.orchestrator._handle_file_ingestion(
                    f"Learn from these {len(temp_files)} files",
                    {
                        'session_id': st.session_state.get('session_id', 'default'),
                        'processing_preferences': preferences
                    },
                    temp_files
                ))

                # Show results
                if response.success:
                    st.success("✨ Brain training completed successfully!")

                    # Show processing summary
                    if hasattr(response, 'processing_summary'):
                        with st.expander("📊 Processing Summary"):
                            st.json(response.processing_summary)

                    # Show training insights
                    if hasattr(response, 'training_insights'):
                        st.subheader("💡 Training Insights")
                        for insight in response.training_insights:
                            st.info(insight)

                    # Show conversation updates
                    if hasattr(response, 'conversation_updates'):
                        with st.expander("💬 Training Conversation"):
                            for update in response.conversation_updates:
                                if update.type == "processing_insight":
                                    st.write(f"🤔 **Sophia**: {update.content}")
                                elif update.type == "completion":
                                    st.write(f"✅ **Completed**: {update.content}")

                else:
                    st.error(f"Training encountered issues: {response.error}")

            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    os.unlink(temp_file)
                except:
                    pass

    def _render_contextual_chat(self):
        """Render enhanced chat with context awareness."""

        # Chat history display
        for role, content in st.session_state.chat_history:
            if role == "user":
                st.chat_message("user").markdown(content)
            else:
                st.chat_message("assistant").markdown(content)

        # Enhanced input with suggestions
        col1, col2 = st.columns([4, 1])

        with col1:
            user_input = st.text_input(
                "Chat with Enhanced Sophia:",
                key="enhanced_chat_input",
                placeholder="Ask about your uploaded content, business insights, or request analysis..."
            )

        with col2:
            if st.button("🚀 Send"):
                if user_input:
                    self._process_chat_message(user_input)

        # Quick action buttons
        st.write("**Quick Actions:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("📊 Business Intelligence"):
                self._process_chat_message("Give me a comprehensive business intelligence summary")

        with col2:
            if st.button("🔍 Knowledge Search"):
                search_query = st.text_input("Search knowledge:", key="knowledge_search")
                if search_query:
                    self._process_chat_message(f"What do you know about {search_query}")

        with col3:
            if st.button("🎯 Content Analysis"):
                self._process_chat_message("Analyze the latest content I've uploaded")

        with col4:
            if st.button("💡 Insights"):
                self._process_chat_message("What insights can you share from my knowledge base")

    def _process_chat_message(self, message):
        """Process chat message with enhanced orchestrator."""

        # Add to chat history
        st.session_state.chat_history.append(("user", message))

        # Process with enhanced orchestrator
        with st.spinner("🧠 Sophia is thinking..."):
            response = asyncio.run(self.orchestrator.process_request(
                message,
                {
                    'session_id': st.session_state.get('session_id', 'default'),
                    'chat_history': st.session_state.chat_history
                }
            ))

        # Display response
        if hasattr(response, 'content'):
            st.session_state.chat_history.append(("assistant", response.content))
            st.chat_message("assistant").markdown(response.content)

            # Show additional insights if available
            if hasattr(response, 'knowledge_insights') and response.knowledge_insights:
                with st.expander("💡 Additional Insights"):
                    for insight in response.knowledge_insights:
                        st.info(insight)

            # Show conversation suggestions
            if hasattr(response, 'conversation_suggestions') and response.conversation_suggestions:
                st.write("**💭 You might also ask:**")
                for suggestion in response.conversation_suggestions[:3]:
                    if st.button(suggestion.message, key=f"suggestion_{hash(suggestion.message)}"):
                        self._process_chat_message(suggestion.message)

# Data Models for Brain Training Responses
@dataclass
class BrainTrainingResponse:
    """Response from brain training operations."""
    success: bool
    content: str
    file_processed: Optional[str] = None
    query_processed: Optional[str] = None
    processing_summary: Optional[Dict[str, Any]] = None
    storage_strategy: Optional[Dict[str, Any]] = None
    training_insights: List[str] = field(default_factory=list)
    retrieval_results: List[Dict[str, Any]] = field(default_factory=list)
    knowledge_insights: List[str] = field(default_factory=list)
    conversation_suggestions: List[Dict[str, str]] = field(default_factory=list)
    conversation_updates: List[Dict[str, Any]] = field(default_factory=list)
    cross_references: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

# Usage Example
if __name__ == "__main__":
    # Initialize enhanced system
    orchestrator = SophiaEnhancedOrchestrator()

    # Example: Process file upload
    response = await orchestrator.process_request(
        "Learn from this business report and extract key insights",
        context={'session_id': 'user123'},
        files=['./reports/q3_business_report.pdf']
    )

    print(f"Training completed: {response.success}")
    print(f"Insights: {response.training_insights}")

    # Example: Knowledge query
    knowledge_response = await orchestrator.process_request(
        "What insights can you provide about Q3 performance based on the uploaded reports?",
        context={'session_id': 'user123'}
    )

    print(f"Knowledge response: {knowledge_response.content}")
```

## Integration Benefits

### 1. Seamless Business Intelligence Enhancement

- Existing AGNO teams (Sales, Research, Client Success, Market Analysis) now have access to trained content
- Business queries can reference uploaded documents, reports, and analyses
- Cross-functional insights combining live data with learned content

### 2. Conversational Learning Experience

- Natural language interaction during file processing
- Real-time feedback and optimization suggestions
- Adaptive system that learns user preferences

### 3. Intelligent Storage Optimization

- Automatic selection of optimal storage strategies
- Performance prediction and optimization
- Multi-modal content support with specialized handling

### 4. Enhanced Chat Interface

- File upload capabilities integrated into existing chat
- Context-aware conversations referencing learned content
- Quick action buttons for common brain training operations

### 5. Unified Knowledge Base

- Business intelligence and learned content in unified system
- Cross-references between different knowledge domains
- Comprehensive search across all content types

## Deployment Strategy

### Phase 1: Core Integration (Week 1)

1. Deploy enhanced orchestrator alongside existing system
2. Add file upload capability to chat interface
3. Implement basic content ingestion pipeline

### Phase 2: Intelligence Layer (Week 2)

1. Deploy conversational training system
2. Implement storage optimization
3. Add context-aware retrieval

### Phase 3: Advanced Features (Week 3)

1. Cross-content relationship discovery
2. Advanced multi-modal processing
3. Performance optimization and scaling

### Phase 4: Production Optimization (Week 4)

1. Performance monitoring and optimization
2. User experience refinement
3. Advanced analytics and insights

This comprehensive integration transforms Sophia from a business intelligence platform into a complete AI brain training system while preserving all existing capabilities and adding powerful new learning and knowledge management features.
