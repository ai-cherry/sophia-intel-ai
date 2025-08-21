"""
SOPHIA Core Utilities
Utility functions for the SOPHIA AI orchestration platform
"""

def hello_world():
    """
    A simple hello world function to demonstrate code-from-chat capabilities.
    
    Returns:
        str: A greeting message from SOPHIA
    """
    return "Hello World from SOPHIA v4.2! Code-from-chat is working!"

def get_version():
    """
    Get the current SOPHIA version.
    
    Returns:
        str: Version string
    """
    return "4.2.0"

def validate_config(config: dict) -> bool:
    """
    Validate SOPHIA configuration.
    
    Args:
        config (dict): Configuration dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = ['api_keys', 'services', 'deployment']
    return all(key in config for key in required_keys)

