import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    model: str | None
    mcp_url: str
    playwright_mcp_url: str | None
    database_url: str

    @classmethod
    def from_env(cls) -> "Settings":
        host = os.getenv("MCP_HOST", "127.0.0.1")
        port = os.getenv("MCP_PORT", "8000")
        mcp_url = os.getenv("MCP_URL")

        if not mcp_url or "{" in mcp_url:
            mcp_url = f"http://{host}:{port}/mcp"

        playwright_mcp_url = os.getenv("PLAYWRIGHT_MCP_URL") or None

        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://rag:rag@localhost:5432/rag",
        )

        return cls(
            base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
            model=os.getenv("LMSTUDIO_MODEL") or None,
            mcp_url=mcp_url,
            playwright_mcp_url=playwright_mcp_url,
            database_url=database_url,
        )
