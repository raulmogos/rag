#!/usr/bin/env python3
import argparse
import asyncio
import sys

from rag.agent import MainAgent
from rag.bootstrap import AgentBootstrapError, build_agent_runtime
from rag.config import Settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Chat with a LangChain agent backed by LM Studio."
    )
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Single-turn prompt. Omit to start an interactive chat session.",
    )
    parser.add_argument(
        "--model",
        help="Override LM Studio model id (defaults to first loaded model).",
    )
    return parser


async def run() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = Settings.from_env()

    try:
        llm, tools, model, tool_count = await build_agent_runtime(settings, args.model)
    except AgentBootstrapError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    agent = MainAgent(llm=llm, tools=tools)
    print(f"Connected to LM Studio model: {model}")
    print(f"Loaded {tool_count} tools (including MCP server tools)\n")

    if args.prompt:
        print(await agent.achat(args.prompt))
        return 0

    print("Interactive mode. Type 'exit' or 'quit' to stop.\n")
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue
        if user_input.lower() in {"exit", "quit"}:
            break

        try:
            print(f"Agent: {await agent.achat(user_input)}\n")
        except Exception as exc:
            print(f"Agent error: {exc}\n", file=sys.stderr)

    return 0


def main() -> int:
    return asyncio.run(run())


if __name__ == "__main__":
    raise SystemExit(main())
