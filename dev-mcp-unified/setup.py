"""
Setup script for dev-mcp-unified
"""

from setuptools import setup, find_packages

setup(
    name="dev-mcp-unified",
    version="1.0.0",
    description="Unified MCP Server for Local AI Coding Assistants",
    author="Sophia AI",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.23.0",
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "PyYAML>=6.0",
        "chromadb>=0.4.0",
        "watchdog>=3.0.0",
        "anthropic>=0.18.0",
        "openai>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp=mcp:main",
        ],
    },
    package_data={
        "": ["*.yaml", "*.json"],
    },
)