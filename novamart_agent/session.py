"""Programmatic conversation driver used by the CLI and the eval runner."""

import uuid
from dataclasses import dataclass, field

from google.adk.runners import InMemoryRunner
from google.genai import types

from novamart_agent.agent import root_agent
from novamart_agent.config import PERSONAS

APP = "novamart_assist"


@dataclass
class Turn:
    answer: str
    tool_calls: list[dict] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)


class AgentSession:
    def __init__(self, role: str = "associate"):
        self._runner = InMemoryRunner(agent=root_agent, app_name=APP)
        self._role = role
        self._user = f"employee-{role}"
        self._session_id: str | None = None

    async def _ensure_session(self) -> str:
        if self._session_id is None:
            session = await self._runner.session_service.create_session(
                app_name=APP,
                user_id=self._user,
                state=dict(PERSONAS[self._role]),
                session_id=str(uuid.uuid4()),
            )
            self._session_id = session.id
        return self._session_id

    async def ask(self, text: str) -> Turn:
        session_id = await self._ensure_session()
        turn = Turn(answer="")
        message = types.Content(role="user", parts=[types.Part(text=text)])
        async for event in self._runner.run_async(
            user_id=self._user, session_id=session_id, new_message=message
        ):
            for call in event.get_function_calls():
                turn.tool_calls.append({"name": call.name, "args": dict(call.args or {})})
            for resp in event.get_function_responses():
                turn.tool_results.append({"name": resp.name, "response": resp.response})
            if event.is_final_response() and event.content and event.content.parts:
                turn.answer += "".join(p.text or "" for p in event.content.parts if not p.thought)
        return turn
