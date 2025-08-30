from agno import Tool
import subprocess
from pathlib import Path
from typing import Optional

class StartPlayground(Tool):
    """Tool for starting the Agno Playground."""
    
    name = "start_playground"
    description = "Start the Agno Playground server"
    parameters = {
        "type": "object",
        "properties": {
            "port": {
                "type": "integer",
                "description": "Port to run the playground on",
                "default": 7777
            }
        },
        "required": []
    }
    
    async def run(self, port: int = 7777) -> str:
        """Start the Agno Playground."""
        try:
            # Check if playground module exists
            playground_path = Path("app/playground.py")
            if not playground_path.exists():
                return "Playground module not found at app/playground.py"
            
            return f"""
To start the Agno Playground, run:

```bash
python -m app.playground
```

The playground will be available at http://localhost:{port}

Note: This tool provides instructions. The actual server must be started in a terminal.
"""
        except Exception as e:
            return f"Error: {str(e)}"


class StartAgentUI(Tool):
    """Tool for starting the Agno Agent UI."""
    
    name = "start_agent_ui"
    description = "Instructions for starting the Agno Agent UI"
    parameters = {
        "type": "object",
        "properties": {
            "playground_url": {
                "type": "string",
                "description": "URL of the playground server",
                "default": "http://localhost:7777"
            }
        },
        "required": []
    }
    
    async def run(self, playground_url: str = "http://localhost:7777") -> str:
        """Provide instructions for starting Agent UI."""
        return f"""
To start the Agno Agent UI:

1. In a new terminal, run:
```bash
npx create-agent-ui@latest agent-ui
cd agent-ui
pnpm install
pnpm dev
```

2. Open the UI in your browser (usually http://localhost:3000)

3. Configure the endpoint to: {playground_url}

Note: Ensure the Playground is running first at {playground_url}
"""