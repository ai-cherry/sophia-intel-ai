"""
Test the embedding infrastructure components.
"""

import asyncio
import os
from pathlib import Path
from app.memory.embed_router import (
    choose_model_for_chunk, embed_with_cache, MODEL_A, MODEL_B, DIM_A, DIM_B
)
from app.memory.chunking import produce_chunks_for_index, discover_source_files
from app.memory.index_weaviate import upsert_chunks_dual, hybrid_search_merge

async def test_embedding_router():
    """Test the embedding router logic."""
    print("🧪 Testing Embedding Router...")
    
    # Test model selection
    short_text = "def hello(): return 'world'"
    long_text = "x" * 10000  # Long text
    rust_text = "fn main() { println!(\"Hello\"); }"
    
    # Test routing logic
    model1, dim1 = choose_model_for_chunk(short_text)
    assert model1 == MODEL_B and dim1 == DIM_B, "Short text should use Tier B"
    
    model2, dim2 = choose_model_for_chunk(long_text)
    assert model2 == MODEL_A and dim2 == DIM_A, "Long text should use Tier A"
    
    model3, dim3 = choose_model_for_chunk(rust_text, lang="rust")
    assert model3 == MODEL_A and dim3 == DIM_A, "Rust should use Tier A"
    
    model4, dim4 = choose_model_for_chunk(short_text, priority="high")
    assert model4 == MODEL_A and dim4 == DIM_A, "High priority should use Tier A"
    
    print("✅ Embedding router tests passed")

async def test_chunking():
    """Test the chunking functionality."""
    print("🧪 Testing Chunking...")
    
    # Create a test file
    test_content = """
def calculate_sum(a, b):
    \"\"\"Calculate the sum of two numbers.\"\"\"
    return a + b

def calculate_product(a, b):
    \"\"\"Calculate the product of two numbers.\"\"\"
    return a * b

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, value):
        self.result += value
        return self.result
"""
    
    # Test chunk production
    ids, texts, payloads = produce_chunks_for_index(
        filepath="test_calc.py",
        content=test_content,
        priority="high"
    )
    
    assert len(ids) > 0, "Should produce at least one chunk"
    assert len(ids) == len(texts) == len(payloads), "Arrays should have same length"
    assert all(p["priority"] == "high" for p in payloads), "Priority should be preserved"
    assert all(p["lang"] == "python" for p in payloads), "Language should be detected"
    
    print(f"✅ Chunking tests passed - produced {len(ids)} chunks")

async def test_file_discovery():
    """Test file discovery functionality."""
    print("🧪 Testing File Discovery...")
    
    # Test discovery in app directory
    files = discover_source_files(
        root_dir="app",
        include_patterns=["*.py"],
        exclude_patterns=["*test*", "*__pycache__*"]
    )
    
    assert len(files) > 0, "Should find Python files in app directory"
    assert all(f.endswith(".py") for f in files), "Should only find Python files"
    assert not any("test" in f for f in files), "Should exclude test files"
    
    print(f"✅ File discovery tests passed - found {len(files)} files")

async def test_embedding_cache():
    """Test embedding cache functionality."""
    print("🧪 Testing Embedding Cache...")
    
    # Skip if no API key
    if not os.getenv("EMBED_API_KEY") and not os.getenv("VK_TOGETHER"):
        print("⚠️  Skipping embedding cache test - no API key configured")
        return
    
    test_texts = ["test embedding one", "test embedding two"]
    
    # First call - should hit API
    vecs1 = embed_with_cache(test_texts, MODEL_B)
    assert len(vecs1) == 2, "Should return two embeddings"
    assert all(len(v) == DIM_B for v in vecs1), f"Embeddings should have dimension {DIM_B}"
    
    # Second call - should use cache
    vecs2 = embed_with_cache(test_texts, MODEL_B)
    assert vecs1[0] == vecs2[0], "Cached embeddings should be identical"
    
    print("✅ Embedding cache tests passed")

async def test_indexing_and_search():
    """Test the full indexing and search pipeline."""
    print("🧪 Testing Indexing and Search...")
    
    # Skip if no Weaviate or API keys
    if not os.getenv("WEAVIATE_URL"):
        print("⚠️  Skipping indexing test - Weaviate not configured")
        return
    
    if not os.getenv("EMBED_API_KEY") and not os.getenv("VK_TOGETHER"):
        print("⚠️  Skipping indexing test - no embedding API key")
        return
    
    # Create test data
    test_ids = ["test_chunk_1", "test_chunk_2", "test_chunk_3"]
    test_texts = [
        "def authenticate_user(username, password): return check_credentials(username, password)",
        "class UserAuth: def login(self, user, pwd): self.validate(user, pwd)",
        "async function loginUser(email, password) { return await api.authenticate(email, password); }"
    ]
    test_payloads = [
        {"path": "auth.py", "lang": "python", "start_line": 10, "end_line": 12, "chunk_id": "test_chunk_1", "priority": "high"},
        {"path": "models.py", "lang": "python", "start_line": 50, "end_line": 55, "chunk_id": "test_chunk_2", "priority": "medium"},
        {"path": "login.js", "lang": "javascript", "start_line": 1, "end_line": 5, "chunk_id": "test_chunk_3", "priority": "medium"}
    ]
    
    # Index the data
    await upsert_chunks_dual(test_ids, test_texts, test_payloads, lang="python")
    print("  ✓ Indexed test chunks")
    
    # Search for authentication code
    results = await hybrid_search_merge("authentication login", k=3, semantic_weight=0.7)
    assert len(results) > 0, "Should find results for authentication query"
    print(f"  ✓ Found {len(results)} search results")
    
    # Verify result structure
    first_result = results[0]
    assert "prop" in first_result, "Result should have properties"
    assert "score" in first_result, "Result should have score"
    assert "collection" in first_result, "Result should have collection indicator"
    
    print("✅ Indexing and search tests passed")

async def main():
    """Run all tests."""
    print("\n🚀 Testing Embedding Infrastructure\n")
    
    # Run tests in sequence
    await test_embedding_router()
    await test_chunking()
    await test_file_discovery()
    await test_embedding_cache()
    await test_indexing_and_search()
    
    print("\n✨ All embedding infrastructure tests completed!\n")

if __name__ == "__main__":
    asyncio.run(main())