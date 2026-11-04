"""Turn Gemini API failures into a clear message for the employee instead of a crash / HTTP 500.

The full error is logged server-side for Ops; the employee only sees what they can act on.
"""

import logging

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

log = logging.getLogger(__name__)

_BILLING = (
    "NovaMart Assist is unavailable right now: the AI service's billing or credits need attention. "
    "Please contact the IT help desk. In the meantime, check the policy binder or ask your manager."
)
_BUSY = "NovaMart Assist is very busy right now. Please try again in a minute."
_GENERIC = (
    "NovaMart Assist couldn't reach the AI service. Please try again, or contact Ops if it keeps happening."
)

_BY_CODE = {402: _BILLING, 403: _BILLING, 429: _BUSY, 500: _BUSY, 503: _BUSY, 504: _BUSY}


def _code(error: Exception) -> int | None:
    code = getattr(error, "code", None)
    return code if isinstance(code, int) else None


def employee_message(error: Exception) -> str:
    return _BY_CODE.get(_code(error), _GENERIC)


def on_model_error(
    callback_context: CallbackContext, llm_request: LlmRequest, error: Exception
) -> LlmResponse:
    """ADK on_model_error_callback: log the real error, answer the employee gracefully."""
    log.error("Gemini call failed (agent=%s): %r", callback_context.agent_name, error)
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=employee_message(error))]),
        error_code=str(_code(error) or type(error).__name__),
        error_message=str(error)[:500],
    )
