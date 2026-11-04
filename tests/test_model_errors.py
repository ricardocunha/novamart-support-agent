import asyncio
from collections.abc import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import errors

from novamart_agent.agent import build_agent
from novamart_agent.model_errors import employee_message
from novamart_agent.session import AgentSession


def api_error(code: int, status: str, cls=errors.ClientError):
    return cls(code, {"error": {"code": code, "message": "upstream detail", "status": status}})


def test_billing_error_tells_employee_to_contact_help_desk_not_retry():
    msg = employee_message(api_error(402, "RESOURCE_EXHAUSTED"))
    assert "billing" in msg.lower()
    assert "help desk" in msg.lower()


def test_rate_limit_asks_to_retry_shortly():
    assert "try again" in employee_message(api_error(429, "RESOURCE_EXHAUSTED")).lower()


def test_overload_asks_to_retry_shortly():
    msg = employee_message(api_error(503, "UNAVAILABLE", errors.ServerError))
    assert "try again" in msg.lower()


def test_unknown_error_is_generic_and_hides_upstream_detail():
    msg = employee_message(RuntimeError("socket exploded at 0xdeadbeef"))
    assert "0xdeadbeef" not in msg
    assert "ops" in msg.lower()


class FailingLlm(BaseLlm):
    model: str = "fake-failing"

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse]:
        raise api_error(402, "RESOURCE_EXHAUSTED")
        yield  # pragma: no cover  (makes this an async generator)


def test_model_failure_reaches_employee_as_message_not_crash():
    session = AgentSession(role="associate", agent=build_agent(model=FailingLlm()))
    turn = asyncio.run(session.ask("Can I return a jacket?"))
    assert "billing" in turn.answer.lower()
    assert turn.error == "402"
