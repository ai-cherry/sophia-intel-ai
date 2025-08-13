# Contributing to SOPHIA-CORE

## Environment Policy: "Sealed & Versioned" Artifact

**The Python environment is immutable and version-controlled.**

- All dependencies are declared in `pyproject.toml` at the repo root.
- Development tools (pytest, ruff, mypy, etc.) go under `[project.optional-dependencies.dev]`.
- The only way to add or update dependencies is to edit `pyproject.toml` and run `uv lock`.
- Commit both `pyproject.toml` and `uv.lock` in the same PR.
- **Manual installation of packages (pip install, uv pip install, etc.) is forbidden.**
- The virtual environment is created and synced only by Codespaces/devcontainer using `uv venv && uv sync --all-extras`.
- After sync, the environment is made read-only to prevent runtime changes.
- `.venv`, `env/`, and all environment artifacts are never committed (see `.gitignore`).

### To add or update a dependency:
1. Edit `pyproject.toml`.
2. Run `uv lock` to update `uv.lock`.
3. Commit both files in your PR.
4. Let CI validate the environment.

### Forbidden:
- Committing `.venv`, `env/`, or any environment directory.
- Running `pip install`, `uv pip install`, or `uv sync` outside the devcontainer postCreateCommand.

### Enforcement:
- CI will fail if `.venv` is committed or if `uv.lock` is out of sync.
- The environment is made read-only after creation.

**Questions?** Open an issue or ask in the team chat.
