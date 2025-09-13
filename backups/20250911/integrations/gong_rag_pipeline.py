#!/usr/bin/env python3
"""
Gong RAG Pipeline with Intelligent Chunking and Vector Storage
Implements transcript processing, embedding, and AI-powered insights extraction
"""
import asyncio
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from langchain.chains import RetrievalQA
from langchain.embeddings import OpenAIEmbeddings
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Weaviate

# Import our Sophia components
from app.core.enhanced_llm_router import get_llm_router
from app.memory.unified_memory_router import MemoryDomain, get_memory_router
from app.sophia.sophia_orchestrator import SophiaOrchestrator


@dataclass
class TranscriptChunk:
    """Enhanced transcript chunk with metadata"""
    call_id: str
    chunk_id: str
    text: str
    speaker: str
    start_time: float
    end_time: float
    chunk_index: int
    total_chunks: int
    metadata: Dict[str, Any]
    
    def to_document(self) -> Document:
        """Convert to LangChain Document"""
        return Document(
            page_content=self.text,
            metadata={
                "call_id": self.call_id,
                "chunk_id": self.chunk_id,
                "speaker": self.speaker,
                "start_time": self.start_time,
                "end_time": self.end_time,
                "chunk_index": self.chunk_index,
                "total_chunks": self.total_chunks,
                **self.metadata,
            }
        )


@dataclass
class GongInsight:
    """Structured insight from Gong call analysis"""
    call_id: str
    insight_type: str  # risk, opportunity, action_item, sentiment
    title: str
    description: str
    confidence: float
    evidence: List[str]
    recommendations: List[str]
    timestamp: datetime
    

class GongTranscriptProcessor:
    """
    Process Gong transcripts with optimal chunking for LLM analysis
    """
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 128,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Use recursive character text splitter for intelligent chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        
    def chunk_transcript(
        self,
        transcript: Dict[str, Any],
        call_id: str,
    ) -> List[TranscriptChunk]:
        """
        Chunk transcript into optimal sizes for processing
        Preserves speaker context and temporal information
        """
        chunks = []
        
        # Extract transcript segments
        segments = transcript.get("callTranscripts", [{}])[0].get("sentences", [])
        
        if not segments:
            return chunks
            
        # Group by speaker for context preservation
        speaker_blocks = []
        current_block = {
            "speaker": segments[0].get("speakerName", "Unknown"),
            "text": "",
            "start": segments[0].get("start", 0),
            "end": segments[0].get("end", 0),
        }
        
        for segment in segments:
            speaker = segment.get("speakerName", "Unknown")
            text = segment.get("text", "")
            
            if speaker == current_block["speaker"]:
                # Same speaker, append text
                current_block["text"] += " " + text
                current_block["end"] = segment.get("end", current_block["end"])
            else:
                # Speaker change, save block and start new
                if len(current_block["text"]) >= self.min_chunk_size:
                    speaker_blocks.append(current_block)
                    
                current_block = {
                    "speaker": speaker,
                    "text": text,
                    "start": segment.get("start", 0),
                    "end": segment.get("end", 0),
                }
        
        # Don't forget the last block
        if len(current_block["text"]) >= self.min_chunk_size:
            speaker_blocks.append(current_block)
            
        # Now chunk each speaker block
        chunk_index = 0
        total_chunks = sum(
            len(self.text_splitter.split_text(block["text"])) 
            for block in speaker_blocks
        )
        
        for block in speaker_blocks:
            text_chunks = self.text_splitter.split_text(block["text"])
            
            for i, text_chunk in enumerate(text_chunks):
                chunk_id = hashlib.md5(
                    f"{call_id}_{chunk_index}_{text_chunk[:50]}".encode()
                ).hexdigest()
                
                chunks.append(TranscriptChunk(
                    call_id=call_id,
                    chunk_id=chunk_id,
                    text=text_chunk,
                    speaker=block["speaker"],
                    start_time=block["start"],
                    end_time=block["end"],
                    chunk_index=chunk_index,
                    total_chunks=total_chunks,
                    metadata={
                        "speaker_role": self._infer_speaker_role(block["speaker"]),
                    }
                ))
                chunk_index += 1
                
        return chunks
        
    def _infer_speaker_role(self, speaker_name: str) -> str:
        """Infer speaker role from name/context"""
        name_lower = speaker_name.lower()
        
        if any(x in name_lower for x in ["sales", "rep", "ae", "account"]):
            return "sales_rep"
        elif any(x in name_lower for x in ["customer", "client", "prospect"]):
            return "customer"
        elif any(x in name_lower for x in ["manager", "director", "vp", "chief"]):
            return "executive"
        else:
            return "participant"


class GongRAGPipeline:
    """
    RAG Pipeline for Gong transcript analysis
    Integrates with Weaviate for vector storage and Sophia for intelligence
    """
    
    def __init__(
        self,
        weaviate_url: str = "http://localhost:8081",
        openai_api_key: Optional[str] = None,
    ):
        self.weaviate_url = weaviate_url
        
        # Initialize embeddings
        self.embeddings = OpenAIEmbeddings(
            openai_api_key=openai_api_key or os.getenv("OPENAI_API_KEY")
        )
        
        # Initialize vector store
        self.vectorstore = Weaviate(
            client=None,  # Will be initialized in setup
            embedding=self.embeddings,
            index_name="GongTranscripts",
            text_key="text",
        )
        
        # Initialize processors
        self.transcript_processor = GongTranscriptProcessor()
        self.llm_router = get_llm_router()
        self.memory_router = get_memory_router()
        self.sophia = SophiaOrchestrator()
        
    async def setup(self):
        """Initialize connections"""
        import weaviate
        
        # Connect to Weaviate
        self.weaviate_client = weaviate.Client(self.weaviate_url)
        
        # Create schema if needed
        schema = {
            "class": "GongTranscript",
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "call_id", "dataType": ["string"]},
                {"name": "speaker", "dataType": ["string"]},
                {"name": "chunk_index", "dataType": ["int"]},
                {"name": "confidence", "dataType": ["number"]},
            ],
        }
        
        try:
            self.weaviate_client.schema.create_class(schema)
        except:
            pass  # Schema already exists
            
        # Update vectorstore with client
        self.vectorstore._client = self.weaviate_client
        
    async def process_transcript(
        self,
        transcript: Dict[str, Any],
        call_metadata: Dict[str, Any],
    ) -> List[GongInsight]:
        """
        Process a Gong transcript through the RAG pipeline
        """
        call_id = call_metadata.get("id", "unknown")
        
        # 1. Chunk the transcript
        chunks = self.transcript_processor.chunk_transcript(transcript, call_id)
        
        if not chunks:
            return []
            
        # 2. Convert to documents and add to vector store
        documents = [chunk.to_document() for chunk in chunks]
        self.vectorstore.add_documents(documents)
        
        # 3. Store in Sophia's memory system
        await self._store_in_memory(chunks, call_metadata)
        
        # 4. Extract insights using RAG
        insights = await self._extract_insights(chunks, call_metadata)
        
        return insights
        
    async def _store_in_memory(
        self,
        chunks: List[TranscriptChunk],
        call_metadata: Dict[str, Any],
    ):
        """Store processed chunks in Sophia's tiered memory"""
        memory_data = {
            "type": "gong_call",
            "call_id": call_metadata.get("id"),
            "timestamp": datetime.now().isoformat(),
            "participants": call_metadata.get("participants", []),
            "duration": call_metadata.get("duration"),
            "chunk_count": len(chunks),
        }
        
        await self.memory_router.store(
            domain=MemoryDomain.SOPHIA,
            key=f"gong_call_{call_metadata.get('id')}",
            value=memory_data,
            ttl=86400,  # 24 hours in L1 cache
        )
        
    async def _extract_insights(
        self,
        chunks: List[TranscriptChunk],
        call_metadata: Dict[str, Any],
    ) -> List[GongInsight]:
        """Extract insights using RAG and Sophia's intelligence"""
        insights = []
        
        # Create QA chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm_router.get_llm("claude-3-opus"),
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 5}
            ),
            return_source_documents=True,
        )
        
        # Define insight extraction queries
        queries = [
            {
                "type": "risk",
                "prompt": "Identify any deal risks, concerns, or objections mentioned in this call. Focus on customer hesitations, competitive mentions, or timeline issues.",
            },
            {
                "type": "opportunity",
                "prompt": "What opportunities for upselling, expansion, or acceleration were discussed? Include any unmet needs or interest areas.",
            },
            {
                "type": "action_item",
                "prompt": "List all action items, next steps, and commitments made by either party during this call.",
            },
            {
                "type": "sentiment",
                "prompt": "Analyze the overall sentiment and engagement level of the customer. Are they excited, neutral, or concerned?",
            },
        ]
        
        # Extract insights for each query type
        for query_info in queries:
            try:
                result = await asyncio.to_thread(
                    qa_chain.run,
                    query_info["prompt"]
                )
                
                # Parse the response
                insight = GongInsight(
                    call_id=call_metadata.get("id", "unknown"),
                    insight_type=query_info["type"],
                    title=f"{query_info['type'].title()} Analysis",
                    description=result,
                    confidence=0.85,  # Can be calculated based on source relevance
                    evidence=[
                        doc.page_content[:200] 
                        for doc in result.get("source_documents", [])[:3]
                    ] if isinstance(result, dict) else [],
                    recommendations=await self._generate_recommendations(
                        query_info["type"],
                        result
                    ),
                    timestamp=datetime.now(),
                )
                
                insights.append(insight)
                
            except Exception as e:
                print(f"Error extracting {query_info['type']} insights: {e}")
                
        return insights
        
    async def _generate_recommendations(
        self,
        insight_type: str,
        analysis: str,
    ) -> List[str]:
        """Generate actionable recommendations based on insights"""
        recommendations = []
        
        if insight_type == "risk":
            recommendations = [
                "Schedule follow-up to address concerns",
                "Prepare competitive differentiation materials",
                "Involve technical team for proof of concept",
            ]
        elif insight_type == "opportunity":
            recommendations = [
                "Create expansion proposal",
                "Schedule demo of additional features",
                "Connect with economic buyer",
            ]
        elif insight_type == "action_item":
            recommendations = [
                "Send follow-up email with summary",
                "Update CRM with next steps",
                "Set calendar reminders for commitments",
            ]
        elif insight_type == "sentiment":
            if "concerned" in analysis.lower():
                recommendations = [
                    "Escalate to sales manager",
                    "Prepare risk mitigation plan",
                ]
            elif "excited" in analysis.lower():
                recommendations = [
                    "Accelerate deal timeline",
                    "Expand deal scope",
                ]
                
        return recommendations
        
    async def query_insights(
        self,
        query: str,
        call_ids: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Query stored insights using natural language
        """
        # Filter by call IDs if provided
        filter_dict = {}
        if call_ids:
            filter_dict = {"call_id": {"$in": call_ids}}
            
        # Create QA chain with filtering
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm_router.get_llm("claude-3-opus"),
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 10, "where": filter_dict}
            ),
            return_source_documents=True,
        )
        
        # Run query
        result = await asyncio.to_thread(qa_chain.run, query)
        
        return {
            "query": query,
            "answer": result if isinstance(result, str) else result.get("result"),
            "sources": [
                {
                    "call_id": doc.metadata.get("call_id"),
                    "speaker": doc.metadata.get("speaker"),
                    "text": doc.page_content[:200],
                }
                for doc in result.get("source_documents", [])[:5]
            ] if isinstance(result, dict) else [],
            "timestamp": datetime.now().isoformat(),
        }


async def test_rag_pipeline():
    """Test the Gong RAG pipeline"""
    print("🧠 Testing Gong RAG Pipeline")
    print("=" * 60)
    
    pipeline = GongRAGPipeline()
    await pipeline.setup()
    
    # Sample transcript for testing
    sample_transcript = {
        "callTranscripts": [{
            "sentences": [
                {
                    "speakerName": "Sales Rep",
                    "text": "Thank you for joining today. I wanted to discuss how our solution can help with your current challenges.",
                    "start": 0,
                    "end": 5000,
                },
                {
                    "speakerName": "Customer",
                    "text": "Yes, we're particularly concerned about the implementation timeline and integration with our existing systems.",
                    "start": 5000,
                    "end": 10000,
                },
                {
                    "speakerName": "Sales Rep",
                    "text": "I understand. We have a dedicated team that handles integrations and our typical timeline is 4-6 weeks.",
                    "start": 10000,
                    "end": 15000,
                },
                {
                    "speakerName": "Customer",
                    "text": "That sounds reasonable. What about pricing for enterprise customers?",
                    "start": 15000,
                    "end": 18000,
                },
            ]
        }]
    }
    
    sample_metadata = {
        "id": "test_call_123",
        "title": "Discovery Call with Acme Corp",
        "participants": ["Sales Rep", "Customer"],
        "duration": 1800,
    }
    
    print("\n1. Processing sample transcript...")
    insights = await pipeline.process_transcript(sample_transcript, sample_metadata)
    
    print(f"\n2. Extracted {len(insights)} insights:")
    for insight in insights:
        print(f"\n   📌 {insight.insight_type.upper()}: {insight.title}")
        print(f"      {insight.description[:200]}...")
        if insight.recommendations:
            print(f"      Recommendations: {', '.join(insight.recommendations[:2])}")
            
    print("\n3. Testing query interface...")
    query_result = await pipeline.query_insights(
        "What concerns did the customer express?",
        call_ids=["test_call_123"]
    )
    print(f"   Query: {query_result['query']}")
    print(f"   Answer: {query_result['answer'][:200]}...")
    
    print("\n" + "=" * 60)
    print("✅ RAG Pipeline test complete")


if __name__ == "__main__":
    asyncio.run(test_rag_pipeline())