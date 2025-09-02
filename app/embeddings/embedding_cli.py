#!/usr/bin/env python3
"""
Command-line interface for Together AI embeddings.
Usage:
    python embedding_cli.py embed "Your text here" --model m2-bert-8k
    python embedding_cli.py batch input.txt --output embeddings.json
    python embedding_cli.py search "query" --documents docs.txt --top-k 5
    python embedding_cli.py similarity "text1" "text2"
"""

import json
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import numpy as np

from together_embeddings import (
    TogetherEmbeddingService,
    EmbeddingConfig,
    EmbeddingModel
)


def load_texts_from_file(filepath: str) -> List[str]:
    """Load texts from file, one per line."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def save_embeddings_to_file(embeddings: List[List[float]], filepath: str, metadata: dict = None):
    """Save embeddings to JSON file."""
    data = {
        "embeddings": embeddings,
        "dimensions": len(embeddings[0]) if embeddings else 0,
        "count": len(embeddings),
        "metadata": metadata or {}
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def cmd_embed(args):
    """Generate embedding for a single text."""
    service = TogetherEmbeddingService()
    
    # Parse model
    model = None
    if args.model:
        model_map = {
            "m2-bert-32k": EmbeddingModel.M2_BERT_32K,
            "m2-bert-8k": EmbeddingModel.M2_BERT_8K,
            "m2-bert-2k": EmbeddingModel.M2_BERT_2K,
            "bge-large": EmbeddingModel.BGE_LARGE,
            "bge-base": EmbeddingModel.BGE_BASE,
            "uae-large": EmbeddingModel.UAE_LARGE,
            "gte-modernbert": EmbeddingModel.GTE_MODERNBERT,
            "e5-multilingual": EmbeddingModel.E5_MULTILINGUAL,
        }
        model = model_map.get(args.model)
        if not model:
            print(f"Unknown model: {args.model}")
            print(f"Available models: {', '.join(model_map.keys())}")
            return 1
    
    # Generate embedding
    result = service.embed([args.text], model=model, use_cache=not args.no_cache)
    
    # Output
    if args.output:
        save_embeddings_to_file(
            result.embeddings,
            args.output,
            metadata={
                "model": result.model,
                "cached": result.cached,
                "latency_ms": result.latency_ms
            }
        )
        print(f"Saved embedding to {args.output}")
    else:
        print(f"Model: {result.model}")
        print(f"Dimensions: {result.dimensions}")
        print(f"Tokens used: {result.tokens_used}")
        print(f"Latency: {result.latency_ms:.2f}ms")
        print(f"Cached: {result.cached}")
        
        if args.verbose:
            print(f"\nEmbedding vector (first 10 dims):")
            print(result.embeddings[0][:10])
    
    return 0


def cmd_batch(args):
    """Generate embeddings for multiple texts."""
    # Load texts
    if args.input == "-":
        texts = [line.strip() for line in sys.stdin if line.strip()]
    else:
        texts = load_texts_from_file(args.input)
    
    print(f"Loaded {len(texts)} texts")
    
    # Parse model
    model = None
    if args.model:
        model_map = {
            "m2-bert-32k": EmbeddingModel.M2_BERT_32K,
            "m2-bert-8k": EmbeddingModel.M2_BERT_8K,
            "bge-large": EmbeddingModel.BGE_LARGE,
            "bge-base": EmbeddingModel.BGE_BASE,
        }
        model = model_map.get(args.model)
    
    # Generate embeddings
    service = TogetherEmbeddingService()
    result = service.embed(texts, model=model, use_cache=not args.no_cache)
    
    # Save results
    output_file = args.output or "embeddings.json"
    save_embeddings_to_file(
        result.embeddings,
        output_file,
        metadata={
            "model": result.model,
            "texts_count": len(texts),
            "cached": result.cached,
            "latency_ms": result.latency_ms,
            "cache_hits": result.metadata.get("cache_hits", 0),
            "cache_misses": result.metadata.get("cache_misses", 0)
        }
    )
    
    print(f"Generated {len(result.embeddings)} embeddings")
    print(f"Model: {result.model}")
    print(f"Dimensions: {result.dimensions}")
    print(f"Cache hits: {result.metadata.get('cache_hits', 0)}")
    print(f"Cache misses: {result.metadata.get('cache_misses', 0)}")
    print(f"Latency: {result.latency_ms:.2f}ms")
    print(f"Saved to {output_file}")
    
    return 0


def cmd_search(args):
    """Search documents using semantic similarity."""
    # Load documents
    if args.documents:
        documents = load_texts_from_file(args.documents)
    else:
        print("Reading documents from stdin (one per line, end with Ctrl+D):")
        documents = [line.strip() for line in sys.stdin if line.strip()]
    
    if not documents:
        print("No documents provided")
        return 1
    
    print(f"Searching {len(documents)} documents")
    
    # Parse model
    model = None
    if args.model:
        model_map = {
            "m2-bert-8k": EmbeddingModel.M2_BERT_8K,
            "bge-large": EmbeddingModel.BGE_LARGE,
        }
        model = model_map.get(args.model)
    
    # Search
    service = TogetherEmbeddingService()
    results = service.search(
        args.query,
        documents,
        top_k=args.top_k,
        model=model
    )
    
    # Display results
    print(f"\nTop {args.top_k} results for query: '{args.query}'\n")
    for i, (idx, score, doc) in enumerate(results, 1):
        # Truncate long documents for display
        display_doc = doc[:100] + "..." if len(doc) > 100 else doc
        print(f"{i}. [Score: {score:.4f}] (Doc #{idx})")
        print(f"   {display_doc}")
        print()
    
    # Save results if requested
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump([
                {"index": idx, "score": score, "document": doc}
                for idx, score, doc in results
            ], f, indent=2)
        print(f"Results saved to {args.output}")
    
    return 0


def cmd_similarity(args):
    """Calculate similarity between two texts."""
    service = TogetherEmbeddingService()
    
    # Parse model
    model = None
    if args.model:
        model_map = {
            "m2-bert-8k": EmbeddingModel.M2_BERT_8K,
            "bge-large": EmbeddingModel.BGE_LARGE,
            "bge-base": EmbeddingModel.BGE_BASE,
        }
        model = model_map.get(args.model)
    
    # Generate embeddings
    result = service.embed([args.text1, args.text2], model=model)
    
    # Calculate similarity
    similarity = service.similarity(
        result.embeddings[0],
        result.embeddings[1]
    )
    
    print(f"Model: {result.model}")
    print(f"Text 1: {args.text1[:50]}...")
    print(f"Text 2: {args.text2[:50]}...")
    print(f"\nCosine Similarity: {similarity:.4f}")
    
    # Interpretation
    if similarity > 0.9:
        print("Interpretation: Very similar (likely duplicates or paraphrases)")
    elif similarity > 0.7:
        print("Interpretation: Similar (related content)")
    elif similarity > 0.5:
        print("Interpretation: Somewhat similar (same topic)")
    elif similarity > 0.3:
        print("Interpretation: Weakly related")
    else:
        print("Interpretation: Unrelated")
    
    return 0


def cmd_recommend(args):
    """Recommend best model for use case."""
    # Estimate token count (rough approximation)
    token_count = len(args.text.split()) * 1.3
    
    recommended = TogetherEmbeddingService.recommend_model(
        text_length=int(token_count),
        use_case=args.use_case,
        language=args.language
    )
    
    print(f"Text length: ~{int(token_count)} tokens")
    print(f"Use case: {args.use_case}")
    print(f"Language: {args.language}")
    print(f"\nRecommended model: {recommended.value}")
    
    # Model details
    model_info = {
        EmbeddingModel.M2_BERT_32K: "32K context, best for long documents",
        EmbeddingModel.M2_BERT_8K: "8K context, balanced performance",
        EmbeddingModel.BGE_LARGE: "512 tokens, high quality for short texts",
        EmbeddingModel.BGE_BASE: "512 tokens, fast and efficient",
        EmbeddingModel.UAE_LARGE: "512 tokens, maximum accuracy",
        EmbeddingModel.E5_MULTILINGUAL: "514 tokens, 100+ languages",
    }
    
    if recommended in model_info:
        print(f"Details: {model_info[recommended]}")
    
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Together AI Embeddings CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Embed command
    embed_parser = subparsers.add_parser("embed", help="Generate embedding for text")
    embed_parser.add_argument("text", help="Text to embed")
    embed_parser.add_argument("--model", help="Model to use (e.g., m2-bert-8k)")
    embed_parser.add_argument("--output", "-o", help="Output file (JSON)")
    embed_parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    embed_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Batch command
    batch_parser = subparsers.add_parser("batch", help="Generate embeddings for multiple texts")
    batch_parser.add_argument("input", help="Input file (one text per line) or '-' for stdin")
    batch_parser.add_argument("--output", "-o", help="Output file (JSON)")
    batch_parser.add_argument("--model", help="Model to use")
    batch_parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    
    # Search command
    search_parser = subparsers.add_parser("search", help="Search documents semantically")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument("--documents", "-d", help="Documents file (one per line)")
    search_parser.add_argument("--top-k", "-k", type=int, default=5, help="Number of results")
    search_parser.add_argument("--model", help="Model to use")
    search_parser.add_argument("--output", "-o", help="Save results to file")
    
    # Similarity command
    sim_parser = subparsers.add_parser("similarity", help="Calculate similarity between texts")
    sim_parser.add_argument("text1", help="First text")
    sim_parser.add_argument("text2", help="Second text")
    sim_parser.add_argument("--model", help="Model to use")
    
    # Recommend command
    rec_parser = subparsers.add_parser("recommend", help="Recommend best model for use case")
    rec_parser.add_argument("text", help="Sample text")
    rec_parser.add_argument("--use-case", default="general",
                           choices=["rag", "search", "clustering", "classification", "general"])
    rec_parser.add_argument("--language", default="en", help="Language code (e.g., en, zh, multi)")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    commands = {
        "embed": cmd_embed,
        "batch": cmd_batch,
        "search": cmd_search,
        "similarity": cmd_similarity,
        "recommend": cmd_recommend,
    }
    
    try:
        return commands[args.command](args)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())