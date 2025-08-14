# No-BS Architecture Principles

## Core Ethos

- **No Bullshit**: Clear, direct, minimal code. No over-engineering or premature abstraction.
- **Stability First**: Prefer known-good patterns; be extremely careful with core components.
- **MCP-First Design**: All state and context should be accessible via MCP servers.

## Architecture Guardrails

### Code Structure

1. **Single Responsibility**: Every module, class, and function has one clear purpose.
2. **Explicit Dependencies**: No hidden imports or side effects; inject dependencies.
3. **Minimal API Surface**: Keep interfaces narrow and focused.
4. **No Circular Dependencies**: Maintain a clear dependency hierarchy.

### Performance

1. **Identify Bottlenecks**: Use profiling before optimizing.
2. **Async by Default**: Use async/await for I/O operations.
3. **Caching Strategy**: Apply appropriate caching with TTL.
4. **Payload Efficiency**: Minimize data transfer sizes.

### Refactoring Guidelines

1. Always start by mapping the current state (imports, flows, data paths).
2. Propose small, atomic changes with clear scope and risk assessment.
3. Include tests for each changed component.
4. Provide rollback instructions for complex changes.
5. Document architectural decisions in commit messages or ADRs.

### Code Quality

1. **Type Annotations**: Required for all function signatures.
2. **Error Handling**: Explicit error paths and logging.
3. **Test Coverage**: Unit tests for logic, integration tests for flows.
4. **Documentation**: Update READMEs and docstrings.
