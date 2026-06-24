import httpx
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI

from rag.config import Settings
from rag.lmstudio import create_chat_model, resolve_model
from rag.mcp_client import load_all_tools


class AgentBootstrapError(Exception):
    pass


async def build_agent_runtime(
    settings: Settings,
    model_override: str | None = None,
) -> tuple[ChatOpenAI, list[BaseTool], str, int]:
    try:
        model = resolve_model(settings, model_override or settings.model)
    except RuntimeError as exc:
        raise AgentBootstrapError(str(exc)) from exc
    except httpx.HTTPError as exc:
        raise AgentBootstrapError(
            f"Could not reach LM Studio at {settings.base_url}: {exc}"
        ) from exc

    llm = create_chat_model(settings, model)

    try:
        tools = await load_all_tools(settings.mcp_url, settings.playwright_mcp_url)
    except Exception as exc:
        servers = [settings.mcp_url]
        if settings.playwright_mcp_url:
            servers.append(settings.playwright_mcp_url)

        details = str(exc)
        if isinstance(exc, ExceptionGroup):
            details = "; ".join(str(error) for error in exc.exceptions)

        raise AgentBootstrapError(
            f"Could not load MCP tools from {', '.join(servers)}: {details}. "
            "Start MCP servers first (python mcp/server.py and Playwright MCP if enabled)."
        ) from exc

    return llm, tools, model, len(tools)
