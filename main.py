from dotenv import load_dotenv
load_dotenv()

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# Now import the server
from server import mcp
from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn


def run():
    """Run the MCP server with streamable_http transport."""
    # Create the ASGI app
    app = mcp.streamable_http_app()
    
    # Run with uvicorn on 0.0.0.0:8000
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
