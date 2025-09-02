
from pydantic import BaseModel


class EmbeddingRequest(BaseModel):
    text: str
    model: str = "text-embedding-ada-002"
    max_tokens: int = 150

class MemoryStoreRequest(BaseModel):
    content: str
    metadata: dict = {}

class MemorySearchRequest(BaseModel):
    query: str
    filters: dict = {}
    top_k: int = 5

class MemoryUpdateRequest(BaseModel):
    memory_id: str
    content: str
    metadata: dict = {}

class MemoryDeleteRequest(BaseModel):
    memory_id: str

class ChatRequest(BaseModel):
    model: str
    messages: list[dict[str, str]]
    temperature: float | None = 0.7
    max_tokens: int | None = 1000
    stream: bool | None = False
