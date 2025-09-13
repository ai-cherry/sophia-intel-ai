#!/usr/bin/env python3
"""
Complete Gong Integration Test Suite
Tests all components: API client, RAG pipeline, webhook handler, and Sophia integration
"""
import asyncio
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any

# Set environment variables for testing
os.environ["GONG_ACCESS_KEY"] = "TV33BPZ5UN45QKZCZ2UCAKRXHQ6Q3L5N"
os.environ["GONG_CLIENT_SECRET"] = "eyJhbGciOiJIUzI1NiJ9.eyJleHAiOjIwNTQxNTA4ODUsImFjY2Vzc0tleSI6IlRWMzNCUFo1VU40NVFLWkNaMlVDQUtSWEhRNlEzTDVOIn0.zgPvDQQIvU1kvF_9ctjcKuqC5xKhlpZo7MH5v7AYufU"


class GongIntegrationTester:
    """
    Comprehensive test suite for Gong integration
    """
    
    def __init__(self):
        self.test_results = {}
        self.total_tests = 0
        self.passed_tests = 0
        
    def print_header(self, title: str):
        """Print formatted section header"""
        print(f"\n{'=' * 60}")
        print(f"🔧 {title}")
        print('=' * 60)
        
    def print_result(self, test_name: str, passed: bool, details: str = ""):
        """Print test result"""
        self.total_tests += 1
        if passed:
            self.passed_tests += 1
            print(f"   ✅ {test_name}")
        else:
            print(f"   ❌ {test_name}")
        if details:
            print(f"      {details}")
        self.test_results[test_name] = passed
        
    async def test_api_client(self):
        """Test the optimized Gong API client"""
        self.print_header("Testing Gong API Client")
        
        try:
            from app.integrations.gong_optimized_client import GongOptimizedClient
            
            # Test basic connectivity
            print("\n1. Testing API connectivity...")
            async with GongOptimizedClient(use_oauth=False) as client:
                # Test connection
                connected = await client.test_connection()
                self.print_result(
                    "API Connection",
                    connected,
                    "Credentials validated" if connected else "Connection failed"
                )
                
                # Test GET calls endpoint
                print("\n2. Testing GET /v2/calls endpoint...")
                try:
                    from_date = datetime.now() - timedelta(days=30)
                    to_date = datetime.now()
                    
                    response = await client.get_calls(
                        from_date=from_date,
                        to_date=to_date,
                        limit=5
                    )
                    
                    calls = response.get("calls", [])
                    self.print_result(
                        "GET Calls Endpoint",
                        True,
                        f"Retrieved {len(calls)} calls"
                    )
                    
                    # Test transcript endpoint if we have calls
                    if calls:
                        call_id = calls[0].get("id")
                        print(f"\n3. Testing POST /v2/calls/transcript for call {call_id}...")
                        
                        try:
                            transcript = await client.get_call_transcript([call_id])
                            has_transcript = "callTranscripts" in transcript
                            self.print_result(
                                "POST Transcript Endpoint",
                                has_transcript,
                                "Transcript retrieved" if has_transcript else "No transcript data"
                            )
                        except Exception as e:
                            self.print_result("POST Transcript Endpoint", False, str(e)[:100])
                    
                except Exception as e:
                    self.print_result("GET Calls Endpoint", False, str(e)[:100])
                    
                # Test rate limiting
                print("\n4. Testing rate limiting...")
                try:
                    # Make rapid requests to test rate limiter
                    tasks = [client.test_connection() for _ in range(5)]
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    
                    errors = [r for r in results if isinstance(r, Exception)]
                    self.print_result(
                        "Rate Limiting",
                        len(errors) == 0,
                        f"Handled {len(results)} rapid requests"
                    )
                except Exception as e:
                    self.print_result("Rate Limiting", False, str(e)[:100])
                    
        except ImportError as e:
            self.print_result("Import API Client", False, str(e))
            
    async def test_rag_pipeline(self):
        """Test the RAG pipeline for transcript processing"""
        self.print_header("Testing RAG Pipeline")
        
        try:
            from app.integrations.gong_rag_pipeline import (
                GongRAGPipeline,
                GongTranscriptProcessor
            )
            
            # Test transcript chunking
            print("\n1. Testing transcript chunking...")
            processor = GongTranscriptProcessor(chunk_size=256, chunk_overlap=50)
            
            sample_transcript = {
                "callTranscripts": [{
                    "sentences": [
                        {
                            "speakerName": "Sales Rep",
                            "text": "Welcome to our demo. Today I'll show you our key features.",
                            "start": 0,
                            "end": 3000,
                        },
                        {
                            "speakerName": "Customer",
                            "text": "Great! We're particularly interested in the integration capabilities and pricing model.",
                            "start": 3000,
                            "end": 6000,
                        },
                        {
                            "speakerName": "Sales Rep",
                            "text": "Perfect. Let me start with our API integration. We support REST, GraphQL, and webhooks.",
                            "start": 6000,
                            "end": 9000,
                        },
                    ]
                }]
            }
            
            chunks = processor.chunk_transcript(sample_transcript, "test_call_001")
            self.print_result(
                "Transcript Chunking",
                len(chunks) > 0,
                f"Created {len(chunks)} chunks"
            )
            
            # Test RAG pipeline setup
            print("\n2. Testing RAG pipeline initialization...")
            try:
                pipeline = GongRAGPipeline()
                await pipeline.setup()
                self.print_result("RAG Pipeline Setup", True, "Pipeline initialized")
                
                # Test insight extraction
                print("\n3. Testing insight extraction...")
                sample_metadata = {
                    "id": "test_call_001",
                    "title": "Product Demo",
                    "participants": ["Sales Rep", "Customer"],
                    "duration": 1800,
                }
                
                insights = await pipeline.process_transcript(
                    sample_transcript,
                    sample_metadata
                )
                
                self.print_result(
                    "Insight Extraction",
                    len(insights) > 0,
                    f"Extracted {len(insights)} insights"
                )
                
                for insight in insights[:2]:
                    print(f"      - {insight.insight_type}: {insight.title}")
                    
                # Test query interface
                print("\n4. Testing query interface...")
                query_result = await pipeline.query_insights(
                    "What topics were discussed?",
                    call_ids=["test_call_001"]
                )
                
                self.print_result(
                    "Query Interface",
                    "answer" in query_result,
                    "Query processed successfully"
                )
                
            except Exception as e:
                self.print_result("RAG Pipeline Setup", False, str(e)[:100])
                
        except ImportError as e:
            self.print_result("Import RAG Pipeline", False, str(e))
            
    async def test_webhook_handler(self):
        """Test the webhook handler"""
        self.print_header("Testing Webhook Handler")
        
        try:
            from app.api.routers.gong_webhook import (
                GongWebhookHandler,
                GongWebhookPayload,
                GongEventType
            )
            
            # Initialize handler
            print("\n1. Testing webhook handler initialization...")
            handler = GongWebhookHandler()
            
            try:
                await handler.setup()
                self.print_result("Webhook Handler Setup", True, "Handler initialized")
                
                # Test event queuing
                print("\n2. Testing event queuing...")
                test_event = GongWebhookPayload(
                    event_type=GongEventType.CALL_ENDED,
                    event_id="test_event_001",
                    timestamp=datetime.now(),
                    call_id="test_call_001",
                    data={"duration": 1800}
                )
                
                event_key = await handler.queue_event(test_event)
                self.print_result(
                    "Event Queuing",
                    event_key is not None,
                    f"Event queued: {event_key}"
                )
                
                # Test signature verification
                print("\n3. Testing signature verification...")
                payload = b'{"test": "data"}'
                signature = "invalid_signature"
                
                is_valid = handler.verify_signature(payload, signature)
                self.print_result(
                    "Signature Verification",
                    not is_valid,  # Should reject invalid signature
                    "Invalid signature correctly rejected"
                )
                
                await handler.cleanup()
                
            except Exception as e:
                self.print_result("Webhook Handler Setup", False, str(e)[:100])
                
        except ImportError as e:
            self.print_result("Import Webhook Handler", False, str(e))
            
    async def test_sophia_integration(self):
        """Test integration with Sophia orchestrator"""
        self.print_header("Testing Sophia Integration")
        
        try:
            from app.integrations.gong_sophia_bridge import (
                GongSophiaContextProcessor,
                GongAgentMapper,
                GongEventType
            )
            
            # Test agent mapping
            print("\n1. Testing agent mapping...")
            mapper = GongAgentMapper()
            
            agents = mapper.get_agents_for_event(GongEventType.CALL_ENDED)
            self.print_result(
                "Agent Mapping",
                "primary" in agents and "secondary" in agents,
                f"Mapped to {agents.get('primary', 'None').__name__ if 'primary' in agents else 'None'}"
            )
            
            # Test context processor
            print("\n2. Testing context processor...")
            try:
                processor = GongSophiaContextProcessor()
                
                # Test event processing
                test_event = {
                    "event_id": "test_001",
                    "event_type": "call_ended",
                    "call_id": "call_001",
                    "timestamp": datetime.now().isoformat(),
                    "raw_data": {"duration": 1800},
                    "priority": "high",
                }
                
                result = await processor.process_gong_event(test_event)
                
                self.print_result(
                    "Context Processing",
                    result is not None,
                    "Event processed through Sophia"
                )
                
            except Exception as e:
                self.print_result("Context Processing", False, str(e)[:100])
                
        except ImportError as e:
            self.print_result("Import Sophia Bridge", False, str(e))
            
    def print_summary(self):
        """Print test summary"""
        self.print_header("Test Summary")
        
        print(f"\nTotal Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.total_tests - self.passed_tests}")
        print(f"Success Rate: {(self.passed_tests/self.total_tests*100):.1f}%")
        
        print("\n📊 Component Status:")
        components = {
            "API Client": ["API Connection", "GET Calls Endpoint", "Rate Limiting"],
            "RAG Pipeline": ["Transcript Chunking", "Insight Extraction", "Query Interface"],
            "Webhook Handler": ["Event Queuing", "Signature Verification"],
            "Sophia Integration": ["Agent Mapping", "Context Processing"],
        }
        
        for component, tests in components.items():
            passed = sum(1 for t in tests if self.test_results.get(t, False))
            total = len(tests)
            status = "✅" if passed == total else "⚠️" if passed > 0 else "❌"
            print(f"   {status} {component}: {passed}/{total} tests passed")
            
        print("\n" + "=" * 60)
        
        if self.passed_tests == self.total_tests:
            print("🎉 All tests passed! Gong integration is fully operational.")
        elif self.passed_tests > self.total_tests * 0.7:
            print("⚠️ Most tests passed. Some components need attention.")
        else:
            print("❌ Integration needs configuration. Check failed tests above.")


async def main():
    """Run complete integration test suite"""
    print("🚀 GONG INTEGRATION COMPLETE TEST SUITE")
    print("Testing all components of the optimized Gong integration")
    
    tester = GongIntegrationTester()
    
    # Run all test suites
    await tester.test_api_client()
    await tester.test_rag_pipeline()
    await tester.test_webhook_handler()
    await tester.test_sophia_integration()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())