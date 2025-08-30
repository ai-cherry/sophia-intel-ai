# Contributing to SophIA-Intel-AI

Thank you for your interest in contributing to SophIA-Intel-AI! This guide will help you get started.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

## Code of Conduct

We are committed to providing a welcoming and inspiring community for all. Please read and follow our Code of Conduct:

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/sophia-intel-ai.git
   cd sophia-intel-ai
   ```

3. Add upstream remote:
   ```bash
   git remote add upstream https://github.com/originalowner/sophia-intel-ai.git
   ```

4. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Development Process

### Branch Naming Convention

Use descriptive branch names following this pattern:

- `feature/` - New features (e.g., `feature/add-websocket-support`)
- `fix/` - Bug fixes (e.g., `fix/memory-leak-in-search`)
- `docs/` - Documentation updates (e.g., `docs/update-api-examples`)
- `refactor/` - Code refactoring (e.g., `refactor/modularize-swarm-patterns`)
- `test/` - Test additions or fixes (e.g., `test/add-integration-tests`)
- `chore/` - Maintenance tasks (e.g., `chore/update-dependencies`)

### Development Workflow

1. **Create a new branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**:
   - Write clean, readable code
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Run tests locally**:
   ```bash
   # Linting
   ruff check .
   
   # Type checking
   mypy app/
   
   # Unit tests
   pytest tests/unit/
   
   # Integration tests
   pytest tests/integration/
   ```

4. **Commit your changes** (see Commit Guidelines below)

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request**

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semicolons, etc.)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Test additions or corrections
- `build`: Build system changes
- `ci`: CI/CD changes
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(swarms): add consensus mechanism for tie-breaking"

# Bug fix
git commit -m "fix(memory): resolve deduplication collision in supermemory store"

# Documentation
git commit -m "docs(api): update OpenAPI schema for new endpoints"

# With body
git commit -m "refactor(patterns): modularize swarm patterns

- Split improved_swarm.py into separate pattern modules
- Create unified interface for pattern composition
- Update imports in orchestrator"
```

### Commit Message Rules

1. Use present tense ("add feature" not "added feature")
2. Use imperative mood ("move cursor" not "moves cursor")
3. Limit first line to 72 characters
4. Reference issues and PRs in the footer

## Pull Request Process

### Before Submitting

1. **Update from upstream**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Ensure all tests pass**:
   ```bash
   pytest
   ```

3. **Update documentation** if you've changed APIs

4. **Add yourself to CONTRIBUTORS.md** (if first contribution)

### PR Template

When creating a PR, use this template:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] No secrets or API keys in code

## Related Issues
Fixes #123
```

### Review Process

1. At least one maintainer review required
2. All CI checks must pass
3. No merge conflicts
4. Documentation updated if needed

## Testing Guidelines

### Unit Tests

Located in `tests/unit/`. Each module should have corresponding tests:

```python
# tests/unit/test_hybrid_search.py
import pytest
from app.memory.hybrid_search import HybridSearch

def test_semantic_search():
    search = HybridSearch()
    results = search.search("test query", semantic_weight=1.0)
    assert len(results) > 0
```

### Integration Tests

Located in `tests/integration/`. Test component interactions:

```python
# tests/integration/test_api_endpoints.py
import pytest
from fastapi.testclient import TestClient
from app.api.unified_server import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
```

### Property-Based Tests

Use `hypothesis` for property testing:

```python
# tests/property/test_search_properties.py
from hypothesis import given, strategies as st
from app.memory.hybrid_search import HybridSearch

@given(st.floats(min_value=0.0, max_value=1.0))
def test_weight_normalization(weight):
    search = HybridSearch()
    semantic_weight = weight
    bm25_weight = 1.0 - weight
    assert abs((semantic_weight + bm25_weight) - 1.0) < 0.001
```

### Test Coverage

Aim for minimum 80% code coverage:

```bash
pytest --cov=app --cov-report=html
```

## Documentation

### Code Documentation

All public functions and classes need docstrings:

```python
def hybrid_search(query: str, limit: int = 10) -> List[SearchResult]:
    """
    Perform hybrid search combining semantic and BM25 retrieval.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of SearchResult objects sorted by relevance
        
    Raises:
        ValueError: If query is empty or limit < 1
    """
```

### API Documentation

API endpoints are automatically documented via FastAPI:
- Access at `http://localhost:8003/docs`
- Update docstrings in route decorators

### Architecture Documentation

Major architectural decisions should be documented in `docs/architecture/`:
- ADR (Architecture Decision Records) format preferred
- Include context, decision, and consequences

## Environment Variables

Never commit secrets! Use `.env.example` for templates:

```bash
# .env.example
OPENROUTER_API_KEY=sk-or-v1-xxx
PORTKEY_API_KEY=xxx
TOGETHER_API_KEY=xxx
```

## CI/CD Pipeline

Our GitHub Actions workflow runs on every PR:

1. **Linting**: `ruff check`
2. **Type Checking**: `mypy`
3. **Unit Tests**: `pytest tests/unit/`
4. **Integration Tests**: `pytest tests/integration/`
5. **Security Scan**: Check for secrets
6. **Coverage Report**: Minimum 80%

## Getting Help

- **Discord**: Join our community for discussions
- **GitHub Issues**: Report bugs or request features
- **Documentation**: Check `/docs` for detailed guides

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- GitHub contributors page
- Release notes

Thank you for contributing to SophIA-Intel-AI! 🚀