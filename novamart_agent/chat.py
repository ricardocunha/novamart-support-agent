"""Terminal chat. Usage: uv run python -m novamart_agent.chat [--role manager] [--show-tools]"""

import argparse
import asyncio
import json

from novamart_agent.session import AgentSession


async def main(role: str, show_tools: bool) -> None:
    session = AgentSession(role=role)
    print(f"NovaMart Assist — signed in as {role}. Ctrl-D to quit.\n")
    while True:
        try:
            text = input("you › ").strip()
        except EOFError:
            print()
            return
        if not text:
            continue
        turn = await session.ask(text)
        if show_tools:
            for call in turn.tool_calls:
                print(f"  ⚙ {call['name']}({json.dumps(call['args'])})")
        print(f"\nassist › {turn.answer}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--role", choices=["associate", "manager"], default="associate")
    parser.add_argument("--show-tools", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.role, args.show_tools))
