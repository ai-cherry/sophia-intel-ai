#!/usr/bin/env python3
"""
Test script for the unified embedding coordinator.
Verifies all strategies work correctly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.memory.embedding_coordinator import get_embedding_coordinator

def test_coordinator():
    """Test the embedding coordinator with different strategies."""
    
    coordinator = get_embedding_coordinator()
    test_texts = [
        "Short text for testing",
        "A much longer text that would normally trigger the tier A model due to its length and complexity in the auto strategy",
        "中文测试文本",  # Chinese text to test language detection
    ]
    
    print("=" * 60)
    print("EMBEDDING COORDINATOR TEST")
    print("=" * 60)
    
    # Test each strategy
    strategies = ["performance", "accuracy", "hybrid", "auto"]
    
    for strategy in strategies:
        print(f"\n🔍 Testing strategy: {strategy}")
        try:
            result = coordinator.generate_embeddings(
                texts=test_texts,
                strategy=strategy
            )
            
            print(f"  ✅ Strategy '{strategy}' successful")
            print(f"     - Embeddings: {len(result['embeddings'])} vectors")
            print(f"     - Dimension: {result['dimension']}")
            print(f"     - Models used: {set(result['provider_models'].values())}")
            
        except Exception as e:
            print(f"  ❌ Strategy '{strategy}' failed: {e}")
    
    # Test with language and priority hints
    print(f"\n🔍 Testing auto strategy with hints")
    try:
        result = coordinator.generate_embeddings(
            texts=test_texts,
            strategy="auto",
            langs=["en", "en", "zh"],
            priorities=["low", "high", "medium"]
        )
        
        print(f"  ✅ Auto strategy with hints successful")
        print(f"     - Provider models: {result['provider_models']}")
        
    except Exception as e:
        print(f"  ❌ Auto strategy with hints failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Embedding coordinator test completed")
    print("=" * 60)

if __name__ == "__main__":
    test_coordinator()