# sophia_core Architecture

Modules
- `config/`: environment and settings management.
- `agents/`: base agent interface and common behaviors.
- `memory/`: memory interfaces and implementations.
- `swarms/`: swarm foundations and coordination primitives.
- `obs/`: logging, metrics, tracing helpers.
- `utils/`: retry, rate limiters, helpers.

Exports
- Package-level: `BaseAgent`, `BaseMemory`, `BaseSwarm`, `Settings`.

Guidelines
- Use ABCs for base classes and complete type hints.
- Keep package imports light; heavy deps should be optional.
