import asyncio
from agno import Playground
from app.swarms.coding.team import (
    create_coding_team,
    make_coding_swarm,
    make_coding_swarm_pool
)
from app import settings

async def main():
    """Main entry point for the Agno Playground."""
    
    # Create the playground instance
    playground = Playground(
        name="Slim Agno Playground",
        port=settings.PLAYGROUND_PORT
    )
    
    # Register multiple team configurations
    
    # 1. Original Coding Team (backward compatibility)
    coding_team = create_coding_team()
    playground.add_team(coding_team)
    
    # 2. Advanced Coding Swarm with concurrent generators
    advanced_swarm = make_coding_swarm(
        concurrent_models=["coderC"],  # Add Grok as third generator
        include_default_pair=True,     # Keep Coder-A and Coder-B
        include_runner=False            # No runner by default (safety)
    )
    playground.add_team(advanced_swarm)
    
    # 3. Fast pool for quick iterations
    try:
        fast_swarm = make_coding_swarm_pool("fast")
        playground.add_team(fast_swarm)
    except Exception as e:
        print(f"⚠️ Could not create fast swarm: {e}")
    
    # 4. Heavy pool for complex tasks
    try:
        heavy_swarm = make_coding_swarm_pool("heavy")
        playground.add_team(heavy_swarm)
    except Exception as e:
        print(f"⚠️ Could not create heavy swarm: {e}")
    
    # Print startup information
    print(f"🚀 Starting Slim Agno Playground on port {settings.PLAYGROUND_PORT}")
    print(f"📍 Access at: http://localhost:{settings.PLAYGROUND_PORT}")
    print("\n📋 Available teams:")
    print("  1. Coding Team: Original 5-agent team (Lead, Coder-A/B, Critic, Judge)")
    print("  2. Coding Swarm: Advanced team with 3+ concurrent generators")
    print("  3. Coding Swarm (fast): Low-latency pool for quick iterations")
    print("  4. Coding Swarm (heavy): Deep reasoning pool for complex tasks")
    print("\n🔧 CLI Tools:")
    print("  - Debate: python -m app.cli.debate --pool [fast|heavy|balanced] --task 'your task'")
    print("\n🎯 To use Agent UI:")
    print("  1. Run: npx create-agent-ui@latest")
    print(f"  2. Point it to: http://localhost:{settings.PLAYGROUND_PORT}")
    print("\n⚡ Quality Gates:")
    print("  - AccuracyEval: Validates output meets acceptance criteria")
    print("  - ReliabilityEval: Ensures expected tool usage patterns")
    print("  - Runner Gate: Blocks execution without judge approval")
    
    # Start the playground server
    await playground.start()

if __name__ == "__main__":
    asyncio.run(main())