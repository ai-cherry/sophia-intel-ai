"""Routing utilities for the Sophia AI orchestrator.

This module consolidates advanced routing features such as
ML-based task selection and chat task handling into a single place.
Currently the ML components are simplified placeholders that can be
replaced with real models in the future.
"""

from .main import OrchestrationRequest


async def ml_route_task(request: OrchestrationRequest) -> str:
    """Select a service based on task characteristics.

    This is a lightweight placeholder for the ML-based router
    implemented in the previous enhanced orchestrator.
    It returns the target service name to handle the request.
    """
    task_type = request.task_type.lower()

    if task_type == "chat":
        return "chat-service"
    if task_type in {"search", "knowledge"}:
        return "enhanced-search"
    return "neural-engine"
