import os
from dotenv import load_dotenv

load_dotenv()

# Chat/LLM configuration (Portkey → OpenRouter)
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.portkey.ai/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HTTP_REFERER = os.getenv("HTTP_REFERER", "http://localhost:3000")
X_TITLE = os.getenv("X_TITLE", "slim-agno")

# Embeddings configuration (Portkey → Together AI)
EMBED_BASE_URL = os.getenv("EMBED_BASE_URL", "https://api.portkey.ai/v1")
EMBED_API_KEY = os.getenv("EMBED_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "togethercomputer/m2-bert-80M-8k-retrieval")

# Legacy Together API key (for backward compatibility during migration)
TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_EMBED_MODEL = os.getenv("TOGETHER_EMBED_MODEL", "togethercomputer/m2-bert-80M-8k-retrieval")

# Weaviate configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
WEAVIATE_CLASS_CODE = os.getenv("WEAVIATE_CLASS_CODE", "CodeChunk")
WEAVIATE_CLASS_DOC = os.getenv("WEAVIATE_CLASS_DOC", "DocChunk")

# Playground configuration
PLAYGROUND_PORT = int(os.getenv("PLAYGROUND_PORT", "7777"))