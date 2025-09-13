"""Sophia Intel AI Application Package

This import ensures configuration is loaded before anything else
"""

# CRITICAL: Load configuration on package import
# This populates os.environ so all integrations work
from app.core.config import Config

# Force load immediately
Config.load_env()

__version__ = "2.0.0"
__all__ = ["Config"]