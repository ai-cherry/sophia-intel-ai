"""
Demo file for testing agent swarm capabilities
This file will be modified by different swarms to demonstrate their abilities.
"""

def hello_world():
    """Simple function to demonstrate basic functionality."""
    return "Hello, World!"

def add_numbers(a, b):
    """Add two numbers together."""
    return a + b

def multiply_numbers(a, b):
    """Multiply two numbers together - Added by MCP Filesystem Server."""
    return a * b

def divide_numbers(a, b):
    """Divide two numbers - Added by MCP Filesystem Server."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# TODO: Add more functions as requested by agent swarms

if __name__ == "__main__":
    print(hello_world())
    print(f"2 + 3 = {add_numbers(2, 3)}")