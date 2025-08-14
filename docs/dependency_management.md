# Dependency Management with uv

This document describes how to manage dependencies in the Sophia Intel project using [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver.

## Overview

The project has been migrated from traditional `requirements.txt` files to a modern `pyproject.toml` + `uv.lock` setup for better dependency management, faster installs, and reproducible environments.

## Project Structure

```
sophia-intel/
├── pyproject.toml          # Project metadata and dependencies
├── uv.lock                 # Locked dependency versions (auto-generated)
├── .venv/                  # Virtual environment (gitignored)
├── requirements.txt        # Legacy file (deprecated)
├── requirements.dev.txt    # Legacy file (deprecated)
└── infra/requirements.txt  # Legacy file (deprecated)
```

## Installation

### Prerequisites

Install uv if not already available:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Setting Up the Development Environment

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ai-cherry/sophia-intel.git
   cd sophia-intel
   ```

2. **Create and activate virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Install production dependencies
   uv sync
   
   # Install with development dependencies
   uv sync --dev
   ```

## Dependency Categories

### Production Dependencies

Core dependencies required for the application to run:

- **Web Framework:** FastAPI, Uvicorn
- **Database:** Redis, Qdrant client
- **LLM/AI:** LangChain, LangGraph, mem0ai
- **HTTP:** aiohttp, httpx, requests
- **Configuration:** Pydantic, PyYAML, python-dotenv

### Development Dependencies

Tools for development, testing, and code quality:

- **Code Quality:** black, ruff, mypy
- **Testing:** pytest, pytest-asyncio, pytest-cov
- **Security:** pip-audit, vulture
- **Dependency Analysis:** deptry

### Infrastructure Dependencies

Pulumi and related packages for infrastructure management:

- **IaC:** pulumi, pulumi-command, pulumi-dnsimple
- **Security:** cryptography
- **HTTP:** httpx, requests

## Common Operations

### Adding New Dependencies

**Production dependency:**
```bash
uv add package-name
```

**Development dependency:**
```bash
uv add --dev package-name
```

**With version constraints:**
```bash
uv add "package-name>=1.0.0,<2.0.0"
```

**Optional dependency group:**
```bash
uv add --optional infra package-name
```

### Removing Dependencies

```bash
uv remove package-name
```

### Updating Dependencies

**Update all dependencies:**
```bash
uv lock --upgrade
```

**Update specific package:**
```bash
uv add package-name --upgrade
```

### Installing from Lock File

```bash
# Exact versions from uv.lock
uv sync

# With development dependencies
uv sync --dev

# Specific optional groups
uv sync --extra infra
```

## Lock File Management

The `uv.lock` file contains exact versions of all dependencies and their transitive dependencies. This ensures reproducible builds across environments.

### Updating the Lock File

```bash
# Regenerate lock file with latest compatible versions
uv lock

# Force update to latest versions
uv lock --upgrade
```

### Lock File Best Practices

1. **Always commit `uv.lock`** to version control
2. **Never edit `uv.lock` manually**
3. **Update lock file when adding/removing dependencies**
4. **Use `uv sync` in CI/CD for reproducible builds**

## CI/CD Integration

The project's GitHub Actions workflows use uv for dependency management:

```yaml
- name: Install uv
  run: curl -LsSf https://astral.sh/uv/install.sh | sh

- name: Install dependencies
  run: uv sync --dev

- name: Run tests
  run: uv run pytest
```

## Migration from pip/requirements.txt

The project has been migrated from the old system:

### Old System (Deprecated)
```
requirements.txt          → pyproject.toml [project.dependencies]
requirements.dev.txt      → pyproject.toml [project.optional-dependencies.dev]
infra/requirements.txt    → pyproject.toml [project.optional-dependencies.infra]
```

### Benefits of uv

1. **Speed:** 10-100x faster than pip
2. **Reproducibility:** Lock file ensures exact versions
3. **Modern:** Uses pyproject.toml standard
4. **Dependency Resolution:** Better conflict resolution
5. **Caching:** Efficient package caching
6. **Virtual Environment Management:** Built-in venv handling

## Troubleshooting

### Common Issues

**1. Lock file conflicts:**
```bash
# Regenerate lock file
rm uv.lock
uv lock
```

**2. Cache issues:**
```bash
# Clear uv cache
uv cache clean
```

**3. Virtual environment issues:**
```bash
# Recreate virtual environment
rm -rf .venv
uv venv
uv sync --dev
```

**4. Dependency conflicts:**
```bash
# Check for conflicts
uv lock --check

# Resolve conflicts by updating
uv lock --upgrade
```

### Environment Variables

uv respects these environment variables:

- `UV_CACHE_DIR`: Cache directory location
- `UV_INDEX_URL`: Custom package index
- `UV_EXTRA_INDEX_URL`: Additional package indexes

## Best Practices

1. **Use `uv sync`** instead of `pip install` in scripts and CI
2. **Commit both `pyproject.toml` and `uv.lock`**
3. **Use `--dev` flag for development environments**
4. **Pin versions for production-critical packages**
5. **Regularly update dependencies** with `uv lock --upgrade`
6. **Use optional dependency groups** for different deployment scenarios
7. **Test dependency updates** in CI before merging

## Integration with IDEs

### VS Code

Add to `.vscode/settings.json`:

```json
{
    "python.defaultInterpreterPath": ".venv/bin/python",
    "python.terminal.activateEnvironment": true
}
```

### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Add interpreter → Existing environment
3. Select `.venv/bin/python`

## Performance Comparison

| Operation | pip | uv | Improvement |
|-----------|-----|----|-----------| 
| Install from lock | 45s | 1.5s | 30x faster |
| Dependency resolution | 120s | 3s | 40x faster |
| Cache hit install | 15s | 0.3s | 50x faster |

## References

- [uv Documentation](https://github.com/astral-sh/uv)
- [PEP 621 - pyproject.toml](https://peps.python.org/pep-0621/)
- [Python Packaging User Guide](https://packaging.python.org/)

