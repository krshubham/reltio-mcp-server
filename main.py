from dotenv import load_dotenv
load_dotenv()

import sys
import os

# Add the src directory to Python path
src_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src')
sys.path.insert(0, src_path)

# Now import the server
from server import mcp


def run():
    """Run the MCP server with SSE transport."""
    mcp.run(transport="sse")

if __name__ == "__main__":
    run()
