"""
Main entry point for the Gong MCP server.

This module provides a convenient way to start the Gong MCP server.
"""

import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    try:
        import uvicorn
        from server import app

        # Get port from environment or use default
        port = int(os.environ.get("GONG_MCP_PORT", 5001))

        logger.info(f"Starting Gong MCP server on port {port}")
        uvicorn.run(app, host="0.0.0.0", port=port)
    except ImportError as e:
        logger.error(f"Failed to import dependencies: {str(e)}")
        logger.error(
            "Make sure 'fastapi', 'uvicorn', 'httpx', and 'backoff' are installed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        sys.exit(1)
