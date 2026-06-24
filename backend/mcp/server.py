"""Simple MCP server exposing a few text utility tools."""

import os
from dotenv import load_dotenv

from mcp.server.fastmcp import FastMCP

load_dotenv()


MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))

mcp = FastMCP("RAG Utilities", host=MCP_HOST, port=MCP_PORT)


@mcp.tool()
def echo_message(message: str) -> str:
    """Return the same message back to the caller."""
    return message


@mcp.tool()
def reverse_text(text: str) -> str:
    """Reverse the characters in the given text."""
    return text[::-1]


@mcp.tool()
def count_words(text: str) -> int:
    """Count the number of words in the given text."""
    return len(text.split())


if __name__ == "__main__":
    print(f"MCP server listening at http://{MCP_HOST}:{MCP_PORT}/mcp")
    mcp.run(transport="streamable-http")
