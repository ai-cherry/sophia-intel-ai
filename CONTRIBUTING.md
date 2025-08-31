# Contributing to Sophia Intel AI

Thank you for your interest in contributing to Sophia Intel AI! This guide will help you get started with development, testing, and submitting contributions.

## Quick Start

```bash
# Clone and setup
git clone https://github.com/ai-cherry/sophia-intel-ai.git
cd sophia-intel-ai
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest

# Start development
docker-compose up -d
python -m app.api.unified_server
```

## Code Standards

- **Type Hints**: All functions must have type annotations
- **Docstrings**: Google style for all public functions/classes
- **Formatting**: Black (100 char line length)
- **Linting**: Ruff + MyPy
- **Testing**: Minimum 80% coverage

## Project Structure

```
app/                  # Main package (imports as sophia_intel_ai)
├── api/             # API endpoints
│   └── routers/     # Modular routers
├── core/            # Core functionality
├── models/          # Pydantic schemas
├── repositories/    # Data access layer
├── swarms/          # Agent implementations
└── memory/          # Memory systems
```

## Submitting Changes

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and test
4. Run pre-commit: `pre-commit run --all-files`
5. Commit: `git commit -m "feat: your feature"`
6. Push and create PR

## Testing

```bash
pytest -v                    # Run all tests
pytest -m unit              # Unit tests only
pytest --cov=app            # With coverage
```

## Adding Features

See detailed guide in docs/development.md

## Support

- Issues: https://github.com/ai-cherry/sophia-intel-ai/issues
- Discord: Join our community server
- Email: team@sophia-intel.ai
