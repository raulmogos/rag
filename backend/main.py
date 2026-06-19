#!/usr/bin/env python3
import argparse
import sys

import httpx

from rag.agent import MainAgent
from rag.config import Settings
from rag.lmstudio import create_chat_model, resolve_model


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


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    settings = Settings.from_env()

    try:
        model = resolve_model(settings, args.model or settings.model)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except httpx.HTTPError as exc:
        print(
            f"Error: could not reach LM Studio at {settings.base_url} ({exc})",
            file=sys.stderr,
        )
        return 1

    llm = create_chat_model(settings, model)
    agent = MainAgent(llm=llm)
    print(f"Connected to LM Studio model: {model}")

    if args.prompt:
        print(agent.chat(args.prompt))
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
            print(f"Agent: {agent.chat(user_input)}\n")
        except Exception as exc:
            print(f"Agent error: {exc}\n", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
