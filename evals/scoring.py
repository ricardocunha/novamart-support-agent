"""Deterministic checks for one eval case. Cheap, offline, and run on every case."""

import re
from dataclasses import dataclass, field

BRACKET = re.compile(r"\[([^\]]+)\]")
CITATION_ID = re.compile(r"[A-Z]{3}-[A-Z]{3}-\d{3}(?:#[a-z0-9-]+)?")


@dataclass
class Transcript:
    answer: str
    tool_calls: list[dict] = field(default_factory=list)
    retrieved_ids: set[str] = field(default_factory=set)

    @property
    def tools_used(self) -> set[str]:
        return {c["name"] for c in self.tool_calls}

    @property
    def citations(self) -> set[str]:
        # Every doc id inside any [...] counts, so "[A#x, B#y]" can't smuggle in an unretrieved B.
        return {cid for inside in BRACKET.findall(self.answer) for cid in CITATION_ID.findall(inside)}


def score_case(expect: dict, t: Transcript) -> dict:
    cited_docs = {c.split("#")[0] for c in t.citations}
    retrieved_docs = {r.split("#")[0] for r in t.retrieved_ids}
    checks = {
        # Every citation must point at something search actually returned this run.
        "citations_grounded": all(
            c in t.retrieved_ids or ("#" not in c and c in retrieved_docs) for c in t.citations
        ),
    }
    if "tools_called" in expect:
        checks["tools_called"] = set(expect["tools_called"]) <= t.tools_used
    if "tools_not_called" in expect:
        checks["tools_not_called"] = not (set(expect["tools_not_called"]) & t.tools_used)
    if "cites" in expect:
        checks["cites"] = set(expect["cites"]) <= cited_docs
    if "must_include" in expect:
        checks["must_include"] = all(re.search(p, t.answer, re.IGNORECASE) for p in expect["must_include"])
    if "must_not_include" in expect:
        checks["must_not_include"] = not any(
            re.search(p, t.answer, re.IGNORECASE) for p in expect["must_not_include"]
        )
    return {"checks": checks, "passed": all(checks.values())}
