"""
Natural Language Interface for Sophia Swarm System
Provides a user-friendly way to interact with the Swarm system
"""

import time
from typing import Dict, Any, Optional
from .graph import run


def process_natural_language(user_query: str) -> Dict[str, Any]:
    """
    Process a natural language request with the Swarm system.
    This provides a user-friendly way to interact with the system.

    Args:
        user_query: The natural language query to process

    Returns:
        The results from the Swarm system execution
    """
    print(f"🧠 Processing: {user_query}")
    print("⚙️ Swarm system working...")
    start_time = time.time()

    # Run the swarm with the natural language query
    results = run(user_query)

    # Calculate processing time
    duration = time.time() - start_time

    # Format the results for user consumption
    print("\n✅ Swarm process complete!")
    print(f"⏱️ Duration: {duration:.2f} seconds")
    print("📊 Agent outputs:")

    for agent in ["architect", "builder", "tester", "operator"]:
        output_len = len(results.get(agent, ""))
        if output_len > 0:
            print(f"  • {agent.capitalize()}: {output_len} chars")
        else:
            print(f"  • {agent.capitalize()}: not executed")

    return results
