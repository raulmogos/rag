import os
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from rag.agent import MainAgent
from rag.bootstrap import AgentBootstrapError, build_agent_runtime
from rag.config import Settings

settings = Settings.from_env()
llm: ChatOpenAI | None = None
tools: list[BaseTool] | None = None
model_name: str | None = None
tool_count = 0
sessions: dict[str, MainAgent] = {}

cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080",
    ).split(",")
    if origin.strip()
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm, tools, model_name, tool_count

    try:
        llm, tools, model_name, tool_count = await build_agent_runtime(settings)
    except AgentBootstrapError as exc:
        raise RuntimeError(str(exc)) from exc

    sessions.clear()
    yield
    sessions.clear()


app = FastAPI(title="RAG Agent API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    reply: str
    session_id: str


class ResetRequest(BaseModel):
    session_id: str | None = None


class ResetResponse(BaseModel):
    session_id: str


class HealthResponse(BaseModel):
    status: str
    model: str | None
    tool_count: int
    mcp_url: str


def _get_or_create_agent(session_id: str | None) -> tuple[MainAgent, str]:
    if llm is None or tools is None or not model_name:
        raise HTTPException(status_code=503, detail="Agent is not ready.")

    resolved_session_id = session_id or str(uuid.uuid4())
    agent = sessions.get(resolved_session_id)
    if agent is None:
        agent = MainAgent(
            llm=llm,
            tools=tools,
            thread_id=resolved_session_id,
        )
        sessions[resolved_session_id] = agent

    return agent, resolved_session_id


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok" if model_name else "starting",
        model=model_name,
        tool_count=tool_count,
        mcp_url=settings.mcp_url,
    )


@app.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    agent, session_id = _get_or_create_agent(payload.session_id)

    try:
        reply = await agent.achat(payload.message.strip())
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return ChatResponse(reply=reply, session_id=session_id)


@app.post("/api/reset", response_model=ResetResponse)
async def reset(payload: ResetRequest) -> ResetResponse:
    if payload.session_id and payload.session_id in sessions:
        del sessions[payload.session_id]

    new_session_id = str(uuid.uuid4())
    return ResetResponse(session_id=new_session_id)
