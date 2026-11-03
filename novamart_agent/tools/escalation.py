"""Close-the-loop tools: escalation tickets to Ops and the knowledge-gap log.

JSONL files stand in for a ticketing system (e.g. ServiceNow/Jira) and an analytics table (BigQuery).
"""

import json
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

CATEGORIES = {"returns", "shipping", "pricing", "loyalty", "warranty", "safety", "loss_prevention", "other"}
URGENCIES = {"low", "normal", "high"}


class _JsonlStore:
    def __init__(self, path: str | Path, now: Callable[[], datetime] = datetime.now):
        self._path = Path(path)
        self._now = now

    def all(self) -> list[dict]:
        if not self._path.exists():
            return []
        return [json.loads(line) for line in self._path.read_text().splitlines() if line.strip()]

    def _append(self, record: dict) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a") as f:
            f.write(json.dumps(record) + "\n")


class TicketStore(_JsonlStore):
    def create(
        self,
        summary: str,
        category: str,
        urgency: str,
        store_id: str,
        order_id: str | None = None,
        cited_docs: list[str] | None = None,
        raised_by_role: str | None = None,
    ) -> dict:
        if category not in CATEGORIES:
            return {"created": False, "error": "INVALID_CATEGORY", "allowed": sorted(CATEGORIES)}
        if urgency not in URGENCIES:
            return {"created": False, "error": "INVALID_URGENCY", "allowed": sorted(URGENCIES)}

        now = self._now()
        day = now.strftime("%Y%m%d")
        seq = 1 + sum(1 for t in self.all() if t["ticket_id"].startswith(f"OPS-{day}-"))
        ticket = {
            "ticket_id": f"OPS-{day}-{seq:04d}",
            "created_at": now.isoformat(),
            "status": "open",
            "summary": summary,
            "category": category,
            "urgency": urgency,
            "store_id": store_id,
            "raised_by_role": raised_by_role,
            "order_id": order_id,
            "cited_docs": cited_docs or [],
        }
        self._append(ticket)
        return {"created": True, "ticket_id": ticket["ticket_id"], "routed_to": f"Ops queue: {category}"}


class GapLog(_JsonlStore):
    def log(self, question: str, reason: str, store_id: str | None = None) -> dict:
        self._append(
            {
                "logged_at": self._now().isoformat(),
                "question": question,
                "reason": reason,
                "store_id": store_id,
            }
        )
        return {"logged": True}
