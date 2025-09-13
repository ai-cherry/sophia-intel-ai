"""
Enhanced code search with hybrid retrieval and citations.
"""
from agno import Tool
from app.core.circuit_breaker import with_circuit_breaker
from app.memory.index_weaviate import hybrid_search_merge
class CodeSearch(Tool):
    """Tool for searching code with hybrid BM25 + vector search."""
    name = "code_search"
    description = "Search for code snippets using hybrid semantic and keyword search"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant code",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 8,
            },
            "semantic_weight": {
                "type": "number",
                "description": "Weight for semantic search (0-1, default 0.65)",
                "default": 0.65,
                "minimum": 0.0,
                "maximum": 1.0,
            },
            "show_citations": {
                "type": "boolean",
                "description": "Include inline citations in results",
                "default": True,
            },
        },
        "required": ["query"],
    }
    @with_circuit_breaker("database")
    @with_circuit_breaker("database")
    async def run(
        self,
        query: str,
        limit: int = 8,
        semantic_weight: float = 0.65,
        show_citations: bool = True,
    ) -> str:
        """
        Search for code using hybrid retrieval from dual collections.
        Args:
            query: The search query
            limit: Maximum number of results
            semantic_weight: Balance between semantic (1.0) and keyword (0.0) search
            show_citations: Whether to include citation markers
        Returns:
            Formatted string with search results and citations
        """
        try:
            # Perform hybrid search across both collections
            results = await hybrid_search_merge(
                query=query, k=limit, semantic_weight=semantic_weight
            )
            if not results:
                return "No code snippets found matching your query."
            # Format results with citations
            output = []
            citations = []
            for i, result in enumerate(results, 1):
                props = result.get("prop", {})
                content = props.get("content", "")
                path = props.get("path", "Unknown")
                start_line = props.get("start_line", 0)
                end_line = props.get("end_line", 0)
                lang = props.get("lang", "")
                collection = result.get("collection", "?")
                score = result.get("score", 0.0)
                # Create citation reference
                citation_ref = f"[{i}]" if show_citations else ""
                citations.append(f"{citation_ref} {path}:{start_line}-{end_line}")
                # Truncate long content but preserve structure
                if len(content) > 600:
                    # Try to break at a natural boundary
                    truncated = content[:550]
                    last_newline = truncated.rfind("\n")
                    if last_newline > 400:
                        content = truncated[:last_newline] + "\n... (truncated)"
                    else:
                        content = truncated + "..."
                output.append(
                    f"**Result {i}** {citation_ref} (score: {score:.3f}, tier: {collection})\n"
                    f"📁 {path}:{start_line}-{end_line} [{lang}]\n"
                    f"```{lang}\n{content}\n```"
                )
            # Add citations section if enabled
            result_text = "\n\n".join(output)
            if show_citations and citations:
                result_text += "\n\n**Citations:**\n" + "\n".join(citations)
            # Add search metadata
            result_text += f"\n\n_Search: hybrid (sem={semantic_weight:.1f}, bm25={1-semantic_weight:.1f}), {len(results)} results_"
            return result_text
        except Exception as e:
            return f"Error searching code: {str(e)}"
class SmartCodeSearch(CodeSearch):
    """
    Enhanced code search with automatic query expansion and reranking.
    """
    name = "smart_code_search"
    description = (
        "Intelligent code search with query understanding and result reranking"
    )
    async def run(
        self,
        query: str,
        limit: int = 8,
        semantic_weight: float = 0.65,
        show_citations: bool = True,
    ) -> str:
        """
        Smart search with query expansion and multiple search strategies.
        Args:
            query: The search query
            limit: Maximum number of results
            semantic_weight: Balance between semantic and keyword search
            show_citations: Whether to include citation markers
        Returns:
            Enhanced search results with smart ranking
        """
        try:
            # Detect query intent
            is_implementation = any(
                word in query.lower()
                for word in ["implement", "function", "method", "class", "def", "async"]
            )
            is_usage = any(
                word in query.lower()
                for word in ["use", "call", "invoke", "example", "usage"]
            )
            is_error = any(
                word in query.lower()
                for word in ["error", "bug", "fix", "issue", "problem", "exception"]
            )
            # Adjust search parameters based on intent
            if is_implementation:
                # Favor semantic search for implementations
                semantic_weight = min(0.8, semantic_weight + 0.15)
            elif is_usage:
                # Balance for usage examples
                semantic_weight = 0.5
            elif is_error:
                # Favor keyword search for error messages
                semantic_weight = max(0.3, semantic_weight - 0.2)
            # Run primary search
            primary_results = await hybrid_search_merge(
                query=query, k=limit, semantic_weight=semantic_weight
            )
            # If few results, try alternative search strategy
            if len(primary_results) < limit // 2:
                # Try with opposite weight
                alt_weight = 1.0 - semantic_weight
                alt_results = await hybrid_search_merge(
                    query=query, k=limit // 2, semantic_weight=alt_weight
                )
                # Merge results, preferring primary
                seen_ids = {r.get("prop", {}).get("chunk_id") for r in primary_results}
                for r in alt_results:
                    if r.get("prop", {}).get("chunk_id") not in seen_ids:
                        primary_results.append(r)
                        if len(primary_results) >= limit:
                            break
            # Format results using parent class method
            return await super().run(
                query=query,
                limit=limit,
                semantic_weight=semantic_weight,
                show_citations=show_citations,
            )
        except Exception:
            # Fallback to basic search
            return await super().run(query, limit, semantic_weight, show_citations)
