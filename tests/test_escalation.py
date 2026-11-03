from datetime import datetime

from novamart_agent.tools.escalation import GapLog, TicketStore

NOW = datetime(2026, 11, 3, 10, 30)


def store(tmp_path):
    return TicketStore(tmp_path / "tickets.jsonl", now=lambda: NOW)


def test_create_ticket_returns_id_and_persists(tmp_path):
    s = store(tmp_path)
    result = s.create(
        summary="Customer's lamp is 14 business days late",
        category="shipping",
        urgency="normal",
        store_id="S-042",
        order_id="NM-1009",
        cited_docs=["POL-SHP-006"],
    )
    assert result["created"] is True
    assert result["ticket_id"] == "OPS-20261103-0001"
    [saved] = s.all()
    assert saved["order_id"] == "NM-1009"
    assert saved["cited_docs"] == ["POL-SHP-006"]
    assert saved["store_id"] == "S-042"


def test_ticket_ids_increment(tmp_path):
    s = store(tmp_path)
    s.create(summary="a", category="other", urgency="low", store_id="S-1")
    second = s.create(summary="b", category="other", urgency="low", store_id="S-1")
    assert second["ticket_id"] == "OPS-20261103-0002"


def test_invalid_category_is_rejected_without_writing(tmp_path):
    s = store(tmp_path)
    result = s.create(summary="x", category="banana", urgency="low", store_id="S-1")
    assert result["created"] is False
    assert result["error"] == "INVALID_CATEGORY"
    assert s.all() == []


def test_invalid_urgency_is_rejected(tmp_path):
    result = store(tmp_path).create(summary="x", category="other", urgency="asap", store_id="S-1")
    assert result["error"] == "INVALID_URGENCY"


def test_gap_log_records_question(tmp_path):
    log = GapLog(tmp_path / "gaps.jsonl", now=lambda: NOW)
    log.log(question="Can customers return opened paint?", reason="no matching policy", store_id="S-042")
    [gap] = log.all()
    assert gap["question"] == "Can customers return opened paint?"
    assert gap["reason"] == "no matching policy"
    assert gap["logged_at"] == "2026-11-03T10:30:00"
