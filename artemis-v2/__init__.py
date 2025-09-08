"""
Artemis v2 - Technical Development Platform
===========================================

A specialized AI system for all coding, testing, debugging, and deployment tasks.

Core Capabilities:
- Code generation and implementation
- Testing and quality assurance
- Debugging and troubleshooting
- Deployment and DevOps
"""

__version__ = "2.0.0"
__author__ = "Artemis Development Team"

from .core import CodeGenerator, Debugger, DeploymentEngine, TestFramework
from .frameworks import FrameworkManager
from .languages import LanguageManager

__all__ = [
    "CodeGenerator",
    "TestFramework",
    "Debugger",
    "DeploymentEngine",
    "LanguageManager",
    "FrameworkManager",
]
