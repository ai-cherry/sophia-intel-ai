"""
Security package for SOPHIA Intel
"""

from .prompt_injection_detector import detector, check_prompt_safety

__all__ = ['detector', 'check_prompt_safety']
