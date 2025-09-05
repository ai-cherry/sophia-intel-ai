# ADR-001: Dependency Injection for Service Management

## Status

Accepted

## Context

The AI Orchestra system initially used a global singleton pattern for the ChatOrchestrator, which created several issues:

- Tight coupling between components
- Difficult to test in isolation
- No proper lifecycle management
- Shared state causing race conditions
- Memory leaks from accumulating state

## Decision

We will implement a comprehensive dependency injection (DI) container to manage service lifecycles and dependencies. The DI container will support:

- Three lifecycle types: Transient, Singleton, and Scoped
- Automatic dependency resolution
- Configuration-based service registration
- Connection pooling and session management

## Consequences

### Positive

- **Testability**: Components can be easily mocked and tested in isolation
- **Flexibility**: Services can be swapped or reconfigured without code changes
- **Resource Management**: Proper lifecycle management prevents memory leaks
- **Scalability**: Connection pooling and session limits improve resource utilization
- **Maintainability**: Clear separation of concerns and explicit dependencies

### Negative

- **Complexity**: Additional abstraction layer to understand
- **Performance**: Minimal overhead from dependency resolution
- **Learning Curve**: Developers need to understand DI patterns

## Implementation

```python
# Service registration
container = DIContainer()
container.register_singleton(IChatOrchestrator, ChatOrchestrator)
container.register_transient(ICommandDispatcher, CommandDispatcher)
container.register_scoped(ISessionManager, SessionManager)

# Service resolution
orchestrator = await container.resolve(IChatOrchestrator)
```

## References

- Martin Fowler's Inversion of Control Containers
- Microsoft's Dependency Injection documentation
- Spring Framework DI patterns
