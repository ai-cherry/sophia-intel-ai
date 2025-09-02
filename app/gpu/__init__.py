"""
Sophia Intel AI GPU Module
Lambda Labs integration for heavy AI workloads
"""

from .lambda_executor import LambdaLabsGPUExecutor, execute_gpu_task, gpu_executor

__all__ = ["LambdaLabsGPUExecutor", "gpu_executor", "execute_gpu_task"]
