import uuid

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from rag.tools import AGENT_TOOLS

DEFAULT_SYSTEM_PROMPT = """You are a helpful assistant running locally via LM Studio.
Use tools when they help answer accurately. Keep responses concise and practical.
For local weather, call get_local_coordinates first, then pass those values to get_weather.
For simple static web pages, prefer fetch_url. For JavaScript-heavy pages, interactions, or
screenshots, use Playwright MCP tools (prefixed with playwright_, e.g. playwright_browser_navigate).
Other MCP tools (echo_message, reverse_text, count_words) come from the rag_utilities server."""


def _extract_response(messages: list) -> str:
    for message in reversed(messages):
        if not isinstance(message, AIMessage) or not message.content:
            continue

        content = message.content
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = [
                block.get("text", "")
                for block in content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            return "".join(text_parts)

        return str(content)

    return ""


class MainAgent:
    def __init__(
        self,
        llm: ChatOpenAI,
        tools: list[BaseTool] | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        thread_id: str | None = None,
    ) -> None:
        self.checkpointer = InMemorySaver()
        self.thread_id = thread_id or str(uuid.uuid4())
        self.graph = create_agent(
            model=llm,
            tools=tools or AGENT_TOOLS,
            system_prompt=system_prompt,
            checkpointer=self.checkpointer,
        )

    def reset(self) -> None:
        self.thread_id = str(uuid.uuid4())

    def chat(self, user_message: str) -> str:
        result = self.graph.invoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": self.thread_id}},
        )
        return _extract_response(result["messages"])

    async def achat(self, user_message: str) -> str:
        result = await self.graph.ainvoke(
            {"messages": [HumanMessage(content=user_message)]},
            config={"configurable": {"thread_id": self.thread_id}},
        )
        return _extract_response(result["messages"])
