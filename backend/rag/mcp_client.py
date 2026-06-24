import asyncio

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient

from rag.tools import AGENT_TOOLS


def _build_mcp_servers(
    mcp_url: str,
    playwright_mcp_url: str | None,
) -> dict[str, dict[str, str]]:
    servers: dict[str, dict[str, str]] = {
        "rag_utilities": {
            "transport": "http",
            "url": mcp_url,
        }
    }

    if playwright_mcp_url:
        servers["playwright"] = {
            "transport": "http",
            "url": playwright_mcp_url,
        }

    return servers


async def load_mcp_tools(
    mcp_url: str,
    playwright_mcp_url: str | None = None,
) -> list[BaseTool]:
    client = MultiServerMCPClient(
        _build_mcp_servers(mcp_url, playwright_mcp_url),
        tool_name_prefix=True,
    )
    return await client.get_tools()


async def load_all_tools(
    mcp_url: str,
    playwright_mcp_url: str | None = None,
) -> list[BaseTool]:
    mcp_tools = await load_mcp_tools(mcp_url, playwright_mcp_url)
    return [*AGENT_TOOLS, *mcp_tools]


def load_all_tools_sync(
    mcp_url: str,
    playwright_mcp_url: str | None = None,
) -> list[BaseTool]:
    return asyncio.run(load_all_tools(mcp_url, playwright_mcp_url))
