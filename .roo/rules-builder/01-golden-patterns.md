# Golden Patterns for SOPHIA Features

## FastAPI Patterns

### API Route Structure

```python
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/v1/resource", tags=["resource"])

class ResourceModel(BaseModel):
    id: str
    name: str
    # Other fields

@router.get("/", response_model=List[ResourceModel])
async def list_resources(
    limit: int = 10,
    offset: int = 0,
    # dependencies
):
    """List resources with pagination."""
    # Implementation

@router.post("/", response_model=ResourceModel, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource: ResourceModel,
    # dependencies
):
    """Create a new resource."""
    # Implementation
```

### Dependency Injection

```python
from fastapi import Depends
from typing import Annotated

async def get_service(config=Depends(get_config)):
    return Service(config)

@router.get("/")
async def endpoint(service: Annotated[ServiceClass, Depends(get_service)]):
    return await service.method()
```

## Next.js Patterns

### Page Structure

```tsx
// pages/resource/[id].tsx
import { GetServerSideProps } from 'next'
import { ResourceDetail } from '@/components/Resource'
import { fetchResource } from '@/lib/api'

export const getServerSideProps: GetServerSideProps = async (context) => {
  const { id } = context.params
  const resource = await fetchResource(id as string)
  
  return {
    props: {
      resource,
    },
  }
}

export default function ResourcePage({ resource }) {
  return <ResourceDetail resource={resource} />
}
```

## MCP Integration Patterns

### Agent-MCP Communication

```python
from libs.mcp_client import MCPClient

class Agent:
    def __init__(self, mcp_client: MCPClient):
        self.mcp_client = mcp_client
        
    async def process_query(self, query: str):
        # Store context
        await self.mcp_client.set_context("user_query", query)
        
        # Retrieve context
        relevant_docs = await self.mcp_client.search_context(query)
        
        # Merge and return
        return self._process_with_context(query, relevant_docs)
```

### MCP Server Implementation

```python
from fastapi import FastAPI, WebSocket
from typing import Dict, List
import json

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    while True:
        data = await websocket.receive_text()
        request = json.loads(data)
        
        if request["action"] == "search":
            results = search_function(request["query"])
            await websocket.send_text(json.dumps({"results": results}))
        elif request["action"] == "store":
            store_function(request["key"], request["value"])
            await websocket.send_text(json.dumps({"success": True}))
```

## Testing Patterns

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def client():
    from fastapi.testclient import TestClient
    from your_app.main import app
    return TestClient(app)

def test_get_resource(client):
    response = client.get("/v1/resource/123")
    assert response.status_code == 200
    assert response.json()["id"] == "123"
```

## Documentation

Every feature should include:

1. API documentation (OpenAPI/Swagger)
2. Architecture diagram for complex features
3. Usage examples in README
4. Updated CHANGELOG entry
