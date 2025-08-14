# Testing Standards for SOPHIA

## Core Testing Principles

1. **Deterministic**: Tests must produce the same result every time
2. **Isolated**: No network calls or external dependencies
3. **Comprehensive**: Test happy paths, edge cases, and error cases
4. **Maintainable**: Clear setup, actions, and assertions

## Dependency Injection and Fakes

### Dependency Injection Pattern

```python
# Production code
class Service:
    def __init__(self, client):
        self.client = client
        
    async def get_data(self, id: str):
        return await self.client.fetch(id)

# Test code
class FakeClient:
    async def fetch(self, id: str):
        return {"id": id, "data": "test"}
        
async def test_service():
    fake_client = FakeClient()
    service = Service(fake_client)
    result = await service.get_data("123")
    assert result["id"] == "123"
```

### Network Ban

NEVER make real network calls in tests:

- Use `unittest.mock` for Python's standard library
- Use `pytest-mock` for pytest fixtures
- Create fake implementations for external services

```python
@pytest.fixture
def mock_http_client(monkeypatch):
    mock_client = AsyncMock()
    mock_client.get.return_value = AsyncMock(
        status_code=200,
        json=AsyncMock(return_value={"data": "test"})
    )
    monkeypatch.setattr("your_module.http_client", mock_client)
    return mock_client
```

## Controlling Time and Randomness

### Time Control

```python
from unittest.mock import patch
import time

def test_with_fixed_time():
    fixed_time = 1628000000
    with patch("time.time", return_value=fixed_time):
        # Test code that uses time.time()
```

### Stable Seeds for Randomness

```python
import random

@pytest.fixture(autouse=True)
def fixed_random_seed():
    random.seed(42)  # Use a fixed seed for tests
    yield
    random.seed()  # Reset seed after test
```

## Temporary Files and Directories

```python
import tempfile
import os
import pytest

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield tmpdirname
        
def test_file_operations(temp_dir):
    file_path = os.path.join(temp_dir, "test_file.txt")
    with open(file_path, "w") as f:
        f.write("test content")
    
    # Test code that reads/writes files
```

## Test Types and Organization

### Unit Tests

- One test file per source file
- Naming convention: `test_<module_name>.py`
- Test each function/method in isolation

### Integration Tests

- Test interactions between components
- Minimal set to verify key flows
- Use fakes instead of mocks where possible

### Fixture Organization

```
tests/
  conftest.py  # Shared fixtures
  unit/
    conftest.py  # Unit-test specific fixtures
    test_module1.py
    test_module2.py
  integration/
    conftest.py  # Integration-test specific fixtures
    test_flow1.py
    test_flow2.py
```

## Running Tests

Always use the `scripts/qa/checks.sh` script, which runs:

1. Ruff (linting)
2. Mypy (type checking)
3. Pytest (unit and integration tests)

Individual test commands:

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/unit/test_module.py

# Run specific test function
python -m pytest tests/unit/test_module.py::test_function

# Run with coverage
python -m pytest --cov=your_module tests/
```
