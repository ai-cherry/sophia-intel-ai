from agno import Tool
from typing import Optional
from app.memory import embed_together, index_weaviate

class CodeSearch(Tool):
    """Tool for searching code in the vector database."""
    
    name = "code_search"
    description = "Search for code snippets in the vector database"
    parameters = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant code"
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of results to return",
                "default": 5
            }
        },
        "required": ["query"]
    }
    
    async def run(self, query: str, limit: int = 5) -> str:
        """
        Search for code snippets using semantic search.
        
        Args:
            query: The search query
            limit: Maximum number of results
            
        Returns:
            Formatted string with search results
        """
        try:
            # Generate embedding for the query
            embeddings = await embed_together.embed_text([query])
            query_vector = embeddings[0]
            
            # Search in Weaviate
            results = await index_weaviate.search_by_vector(
                vector=query_vector,
                limit=limit
            )
            
            if not results:
                return "No code snippets found matching your query."
            
            # Format results
            output = []
            for i, result in enumerate(results, 1):
                content = result.get("content", "")
                filepath = result.get("filepath", "Unknown")
                start_line = result.get("start_line", 0)
                end_line = result.get("end_line", 0)
                certainty = result.get("_additional", {}).get("certainty", 0)
                
                output.append(
                    f"**Result {i}** (certainty: {certainty:.2f})\n"
                    f"File: {filepath} (lines {start_line}-{end_line})\n"
                    f"```\n{content[:500]}{'...' if len(content) > 500 else ''}\n```"
                )
            
            return "\n\n".join(output)
            
        except Exception as e:
            return f"Error searching code: {str(e)}"