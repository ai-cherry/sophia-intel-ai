import asyncio
from agno import Playground
from app.swarms.coding.team import create_coding_team
from app import settings

async def main():
    """Main entry point for the Agno Playground."""
    
    # Create the playground instance
    playground = Playground(
        name="Slim Agno Playground",
        port=settings.PLAYGROUND_PORT
    )
    
    # Register the Coding Team
    coding_team = create_coding_team()
    playground.add_team(coding_team)
    
    # Print startup information
    print(f"🚀 Starting Slim Agno Playground on port {settings.PLAYGROUND_PORT}")
    print(f"📍 Access at: http://localhost:{settings.PLAYGROUND_PORT}")
    print("\nAvailable teams:")
    print("  - Coding Team: Software development and code operations")
    print("\nTo use Agent UI:")
    print("  1. Run: npx create-agent-ui@latest")
    print(f"  2. Point it to: http://localhost:{settings.PLAYGROUND_PORT}")
    
    # Start the playground server
    await playground.start()

if __name__ == "__main__":
    asyncio.run(main())