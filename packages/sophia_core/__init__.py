"""
Sophia Core Package - Foundation for AI Agents and Swarms
This package provides core functionality for building AI agents and swarms including:
- Configuration management with environment variables and settings
- Base interfaces for models, memory, tools, agents, and swarms
- Observability with structured logging and metrics
- Utilities for retry logic, circuit breakers, and data redaction
- Core exception classes for consistent error handling
Version: 1.0.0
"""
import logging
from typing import Any, Dict
__version__ = "1.0.0"
__author__ = "Sophia Intelligence AI"
# Configure default logging for the package
logging.getLogger(__name__).addHandler(logging.NullHandler())
# Package-level exports
__all__ = [
    "__version__",
    "__author__",
    "config",
    "models",
    "memory",
    "tools",
    "agents",
    "swarms",
    "obs",
    "utils",
    "exceptions",
    # Explicit base class exports (available at package level)
    "BaseAgent",
    "BaseMemory",
    "BaseSwarm",
    "Settings",
]
# Lazy imports - modules are imported when accessed
def __getattr__(name: str) -> Any:
    """Lazy loading of submodules."""
    if name in __all__:
        if name == "config":
            from . import config
            return config
        elif name == "models":
            from . import models
            return models
        elif name == "memory":
            from . import memory
            return memory
        elif name == "tools":
            from . import tools
            return tools
        elif name == "agents":
            from . import agents
            return agents
        elif name == "swarms":
            from . import swarms
            return swarms
        elif name == "obs":
            from . import obs
            return obs
        elif name == "utils":
            from . import utils
            return utils
        elif name == "exceptions":
            from . import exceptions
            return exceptions
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
# Explicit exports for key base classes
try:
    from .agents.base import BaseAgent  # type: ignore
    from .memory.base import BaseMemory  # type: ignore
    from .swarms.base import BaseSwarm  # type: ignore
    from .config.env import Settings  # type: ignore
except Exception:  # pragma: no cover
    # Keep import-time failures non-fatal for environments missing optional deps
    pass
