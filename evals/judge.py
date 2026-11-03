"""LLM-as-judge: a stronger Gemini model grades faithfulness and correctness on a 1–5 rubric."""

import json

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from novamart_agent.config import JUDGE_MODEL

PASS_THRESHOLD = 4

RUBRIC = """\
You are grading an internal retail support assistant. Be strict and literal.

faithfulness (1-5): Is every factual claim in the ANSWER supported by the TOOL OUTPUTS (policy
sections and order data)? 5 = fully supported; 3 = one minor unsupported detail; 1 = invents facts.
An answer that correctly says "the policy doesn't cover this" is faithful.

correctness (1-5): Does the ANSWER reach the same conclusion and key conditions as the REFERENCE?
5 = same conclusion, key conditions present; 3 = right conclusion, missing an important condition;
1 = wrong conclusion. Wording and extra correct detail don't matter.
"""


class Verdict(BaseModel):
    faithfulness: int = Field(ge=1, le=5)
    correctness: int = Field(ge=1, le=5)
    rationale: str


class Judge:
    def __init__(self, model: str = JUDGE_MODEL):
        self._client = genai.Client()
        self._model = model

    async def grade(self, question: str, answer: str, tool_results: list[dict], reference: str) -> dict:
        prompt = (
            f"QUESTION:\n{question}\n\nTOOL OUTPUTS:\n{json.dumps(tool_results, indent=1, default=str)}\n\n"
            f"REFERENCE:\n{reference}\n\nANSWER:\n{answer}"
        )
        resp = await self._client.aio.models.generate_content(
            model=self._model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=RUBRIC,
                temperature=0,
                response_mime_type="application/json",
                response_schema=Verdict,
            ),
        )
        v: Verdict = resp.parsed
        return {
            **v.model_dump(),
            "passed": v.faithfulness >= PASS_THRESHOLD and v.correctness >= PASS_THRESHOLD,
        }
