"""ADK entry point. `adk web` / `adk run` discover `root_agent` in this module."""

from google.adk.agents import LlmAgent
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.readonly_context import ReadonlyContext
from google.adk.models.google_llm import Gemini
from google.genai import types

from novamart_agent import clock
from novamart_agent.config import AGENT_MODEL, DEFAULT_ROLE, HTTP_RETRY, PERSONAS
from novamart_agent.prompts import INSTRUCTION
from novamart_agent.tools import ALL_TOOLS


def _seed_persona(callback_context: CallbackContext) -> None:
    """Give every new session a signed-in employee (mocked; SSO claims in production)."""
    if "role" not in callback_context.state:
        for key, value in PERSONAS[DEFAULT_ROLE].items():
            callback_context.state[key] = value


def _instruction(ctx: ReadonlyContext) -> str:
    state = ctx.state
    return INSTRUCTION.format(
        employee_name=state.get("employee_name", "employee"),
        role=state.get("role", "associate"),
        store_id=state.get("store_id", "unknown"),
        today=clock.today().strftime("%A %d %B %Y"),
    )


root_agent = LlmAgent(
    name="novamart_assist",
    model=Gemini(model=AGENT_MODEL, retry_options=HTTP_RETRY),
    description="Answers NovaMart store employees' policy and order questions, grounded in company docs.",
    instruction=_instruction,
    tools=ALL_TOOLS,
    before_agent_callback=_seed_persona,
    generate_content_config=types.GenerateContentConfig(temperature=0.1),
)
