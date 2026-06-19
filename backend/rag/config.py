import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    base_url: str
    api_key: str
    model: str | None

    @classmethod
    def from_env(cls) -> "Settings":
        return cls(
            base_url=os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1"),
            api_key=os.getenv("LMSTUDIO_API_KEY", "lm-studio"),
            model=os.getenv("LMSTUDIO_MODEL") or None,
        )
