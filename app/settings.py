import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HTTP_REFERER = os.getenv("HTTP_REFERER", "http://localhost:3000")
X_TITLE = os.getenv("X_TITLE", "slim-agno")

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY", "")
TOGETHER_EMBED_MODEL = os.getenv("TOGETHER_EMBED_MODEL", "togethercomputer/m2-bert-80M-8k-retrieval")

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_API_KEY = os.getenv("WEAVIATE_API_KEY", "")
WEAVIATE_CLASS_CODE = os.getenv("WEAVIATE_CLASS_CODE", "CodeChunk")
WEAVIATE_CLASS_DOC = os.getenv("WEAVIATE_CLASS_DOC", "DocChunk")

PLAYGROUND_PORT = int(os.getenv("PLAYGROUND_PORT", "7777"))