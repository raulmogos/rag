import httpx
from langchain_openai import ChatOpenAI

from rag.config import Settings


def resolve_model(settings: Settings, preferred: str | None) -> str:
    if preferred:
        return preferred

    response = httpx.get(f"{settings.base_url.rstrip('/')}/models", timeout=10.0)
    response.raise_for_status()
    models = response.json().get("data", [])

    if not models:
        raise RuntimeError(
            "No models found in LM Studio. Load a model and start the local server."
        )

    return models[0]["id"]


def create_chat_model(settings: Settings, model: str) -> ChatOpenAI:
    return ChatOpenAI(
        model=model,
        base_url=settings.base_url,
        api_key=settings.api_key,
        temperature=0.2,
    )
