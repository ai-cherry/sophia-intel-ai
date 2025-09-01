"""
Sophia Intel AI GPU Module
Lambda Labs integration for heavy AI workloads
"""

from .lambda_executor import LambdaLabsGPUExecutor, gpu_executor, execute_gpu_task

__all__ = ["LambdaLabsGPUExecutor", "gpu_executor", "execute_gpu_task"]