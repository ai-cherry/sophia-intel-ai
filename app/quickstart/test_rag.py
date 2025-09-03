#!/usr/bin/env python3
"""
Quick Test Script for RAG Pipeline
Phase 2, Week 1-2: Verify RAG pipeline functionality
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from typing import Any

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.basic_rag import BasicRAGPipeline, RAGConfig

from app.core.ai_logger import logger


# Color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_header(message: str):
    """Print a formatted header"""
    logger.info(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    logger.info(f"{Colors.CYAN}{Colors.BOLD}{message}{Colors.END}")
    logger.info(f"{Colors.CYAN}{'='*60}{Colors.END}")


def print_section(message: str):
    """Print a section header"""
    logger.info(f"\n{Colors.BLUE}{message}{Colors.END}")
    logger.info(f"{Colors.BLUE}{'-'*40}{Colors.END}")


def print_success(message: str):
    """Print success message"""
    logger.info(f"{Colors.GREEN}✅ {message}{Colors.END}")


def print_error(message: str):
    """Print error message"""
    logger.info(f"{Colors.RED}❌ {message}{Colors.END}")


def print_info(message: str):
    """Print info message"""
    logger.info(f"{Colors.YELLOW}ℹ️  {message}{Colors.END}")


def test_connection(rag: BasicRAGPipeline) -> bool:
    """Test connections to Weaviate and Ollama"""
    print_section("Testing Connections")

    try:
        stats = rag.get_stats()
        if stats["status"] == "success":
            print_success(f"Connected to Weaviate at {stats['weaviate_url']}")
            print_success(f"LLM Model: {stats['llm_model']}")
            print_success(f"Embedding Model: {stats['embedding_model']}")
            print_info(f"Current document count: {stats['document_count']}")
            return True
        else:
            print_error(f"Connection test failed: {stats.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print_error(f"Connection test failed: {e}")
        return False


def test_ingestion(rag: BasicRAGPipeline) -> bool:
    """Test document ingestion"""
    print_section("Testing Document Ingestion")

    # Sample documents to ingest
    documents = [
        {
            "text": """
            Artificial Intelligence (AI) is the simulation of human intelligence in machines.
            These machines are programmed to think and learn like humans. AI systems can
            perform tasks such as visual perception, speech recognition, decision-making,
            and language translation.
            """,
            "source": "ai_basics.txt"
        },
        {
            "text": """
            Machine Learning is a subset of AI that enables systems to learn and improve
            from experience without being explicitly programmed. It focuses on developing
            computer programs that can access data and use it to learn for themselves.
            Deep Learning is a subset of Machine Learning that uses neural networks.
            """,
            "source": "ml_overview.txt"
        },
        {
            "text": """
            RAG (Retrieval-Augmented Generation) combines the benefits of retrieval-based
            and generative AI models. It retrieves relevant information from a knowledge base
            and uses it to generate more accurate and contextual responses. This approach
            reduces hallucinations and improves the factual accuracy of AI responses.
            """,
            "source": "rag_explained.txt"
        }
    ]

    success_count = 0
    for doc in documents:
        try:
            result = rag.ingest_text(doc["text"], doc["source"])
            if result["status"] == "success":
                print_success(f"Ingested {result['chunks_created']} chunks from {doc['source']}")
                success_count += 1
            else:
                print_error(f"Failed to ingest {doc['source']}: {result.get('error')}")
        except Exception as e:
            print_error(f"Failed to ingest {doc['source']}: {e}")

    print_info(f"Successfully ingested {success_count}/{len(documents)} documents")
    return success_count > 0


def test_queries(rag: BasicRAGPipeline) -> dict[str, Any]:
    """Test various queries and measure performance"""
    print_section("Testing Query and Retrieval")

    test_queries = [
        "What is Artificial Intelligence?",
        "Explain the difference between Machine Learning and Deep Learning",
        "What are the benefits of RAG?",
        "How does a neural network work?",
        "What is Sophia Intel AI?"  # This should trigger "don't know" response
    ]

    results = []
    total_time = 0

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{Colors.PURPLE}Query {i}: {query}{Colors.END}")

        start_time = time.time()
        try:
            response = rag.query(query, return_sources=True)
            elapsed_time = time.time() - start_time
            total_time += elapsed_time

            if response["status"] == "success":
                logger.info(f"{Colors.GREEN}Answer:{Colors.END} {response['answer'][:200]}...")

                if "sources" in response and response["sources"]:
                    logger.info(f"{Colors.CYAN}Sources:{Colors.END}")
                    for source in response["sources"][:2]:  # Show first 2 sources
                        logger.info(f"  • {source['source']}: {source['content'][:100]}...")

                logger.info(f"{Colors.YELLOW}Response time: {elapsed_time:.2f}s{Colors.END}")

                results.append({
                    "query": query,
                    "success": True,
                    "time": elapsed_time,
                    "sources_count": len(response.get("sources", []))
                })
            else:
                print_error(f"Query failed: {response.get('error')}")
                results.append({
                    "query": query,
                    "success": False,
                    "error": response.get("error")
                })
        except Exception as e:
            print_error(f"Query failed: {e}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e)
            })

    # Calculate metrics
    successful_queries = [r for r in results if r.get("success")]
    if successful_queries:
        avg_time = sum(r["time"] for r in successful_queries) / len(successful_queries)
        avg_sources = sum(r.get("sources_count", 0) for r in successful_queries) / len(successful_queries)
    else:
        avg_time = 0
        avg_sources = 0

    return {
        "total_queries": len(test_queries),
        "successful_queries": len(successful_queries),
        "average_response_time": avg_time,
        "average_sources_retrieved": avg_sources,
        "total_time": total_time,
        "results": results
    }


def test_file_ingestion(rag: BasicRAGPipeline) -> bool:
    """Test file ingestion capability"""
    print_section("Testing File Ingestion")

    # Create a test file
    test_file = "test_document.txt"
    test_content = """
    This is a test document for the RAG pipeline.
    
    The document contains multiple paragraphs to test the chunking functionality.
    Each paragraph should be properly processed and stored in the vector database.
    
    Key features being tested:
    - Text splitting and chunking
    - Embedding generation
    - Vector storage in Weaviate
    - Metadata preservation
    
    This test ensures that the file ingestion pipeline works correctly.
    """

    try:
        # Write test file
        with open(test_file, 'w') as f:
            f.write(test_content)

        # Ingest the file
        result = rag.ingest_file(test_file)

        # Clean up
        os.remove(test_file)

        if result["status"] == "success":
            print_success(f"Successfully ingested file: {result['chunks_created']} chunks created")

            # Test query on the ingested content
            response = rag.query("What features are being tested in the test document?")
            if response["status"] == "success":
                print_success("Query on ingested file content successful")
                logger.info(f"Answer: {response['answer'][:200]}...")
            return True
        else:
            print_error(f"File ingestion failed: {result.get('error')}")
            return False

    except Exception as e:
        print_error(f"File ingestion test failed: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)
        return False


def benchmark_performance(rag: BasicRAGPipeline) -> dict[str, Any]:
    """Run performance benchmarks"""
    print_section("Performance Benchmarks")

    benchmarks = {}

    # Test ingestion speed
    print_info("Testing ingestion speed...")
    large_text = " ".join(["This is a test sentence." for _ in range(1000)])
    start_time = time.time()
    result = rag.ingest_text(large_text, "benchmark_doc")
    ingestion_time = time.time() - start_time

    if result["status"] == "success":
        benchmarks["ingestion"] = {
            "chunks": result["chunks_created"],
            "time": ingestion_time,
            "chunks_per_second": result["chunks_created"] / ingestion_time
        }
        print_success(f"Ingestion: {result['chunks_created']} chunks in {ingestion_time:.2f}s")

    # Test query speed
    print_info("Testing query speed...")
    query_times = []
    for i in range(5):
        start_time = time.time()
        rag.query("What is a test sentence?")
        query_times.append(time.time() - start_time)

    avg_query_time = sum(query_times) / len(query_times)
    benchmarks["query"] = {
        "average_time": avg_query_time,
        "min_time": min(query_times),
        "max_time": max(query_times)
    }
    print_success(f"Query: avg {avg_query_time:.2f}s, min {min(query_times):.2f}s, max {max(query_times):.2f}s")

    return benchmarks


def main():
    """Main test execution"""
    parser = argparse.ArgumentParser(description="Test RAG Pipeline")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama service URL")
    parser.add_argument("--weaviate-url", default="http://localhost:8080", help="Weaviate service URL")
    parser.add_argument("--model", default="llama3.2:3b", help="LLM model to use")
    parser.add_argument("--clear", action="store_true", help="Clear existing collection before testing")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmarks")

    args = parser.parse_args()

    print_header("🧪 SOPHIA INTEL AI - RAG PIPELINE TEST")
    logger.info(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Configure RAG
    config = RAGConfig(
        ollama_base_url=args.ollama_url,
        weaviate_url=args.weaviate_url,
        llm_model=args.model
    )

    print_info("Configuration:")
    logger.info(f"  • Ollama URL: {config.ollama_base_url}")
    logger.info(f"  • Weaviate URL: {config.weaviate_url}")
    logger.info(f"  • LLM Model: {config.llm_model}")

    try:
        # Initialize RAG pipeline
        print_section("Initializing RAG Pipeline")
        rag = BasicRAGPipeline(config)
        print_success("RAG pipeline initialized")

        # Clear collection if requested
        if args.clear:
            print_info("Clearing existing collection...")
            rag.clear_collection()

        # Run tests
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "ollama_url": config.ollama_base_url,
                "weaviate_url": config.weaviate_url,
                "model": config.llm_model
            },
            "tests": {}
        }

        # Test 1: Connection
        if test_connection(rag):
            test_results["tests"]["connection"] = "passed"
        else:
            test_results["tests"]["connection"] = "failed"
            print_error("Connection test failed. Exiting...")
            return

        # Test 2: Ingestion
        if test_ingestion(rag):
            test_results["tests"]["ingestion"] = "passed"
        else:
            test_results["tests"]["ingestion"] = "failed"

        # Test 3: Queries
        query_results = test_queries(rag)
        test_results["tests"]["queries"] = query_results

        # Test 4: File Ingestion
        if test_file_ingestion(rag):
            test_results["tests"]["file_ingestion"] = "passed"
        else:
            test_results["tests"]["file_ingestion"] = "failed"

        # Test 5: Benchmarks (optional)
        if args.benchmark:
            benchmark_results = benchmark_performance(rag)
            test_results["benchmarks"] = benchmark_results

        # Print summary
        print_header("📊 TEST SUMMARY")

        print_section("Test Results")
        for test_name, result in test_results["tests"].items():
            if isinstance(result, str):
                status = "✅" if result == "passed" else "❌"
                logger.info(f"{status} {test_name}: {result}")
            elif isinstance(result, dict) and "successful_queries" in result:
                success_rate = result["successful_queries"] / result["total_queries"] * 100
                logger.info(f"📊 Queries: {result['successful_queries']}/{result['total_queries']} ({success_rate:.0f}%)")
                logger.info(f"   • Avg response time: {result['average_response_time']:.2f}s")
                logger.info(f"   • Avg sources retrieved: {result['average_sources_retrieved']:.1f}")

        # Save results to file
        results_file = f"rag_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        print_info(f"Results saved to: {results_file}")

        # Final stats
        stats = rag.get_stats()
        print_section("Final Statistics")
        logger.info(f"Total documents in collection: {stats['document_count']}")

        print_header("✨ RAG PIPELINE TEST COMPLETED")

    except Exception as e:
        print_error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
