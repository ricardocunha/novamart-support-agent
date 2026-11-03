"""ADK function tools. Docstrings and type hints are what Gemini sees as the tool schema.

Each tool is a thin adapter over a plain, unit-tested service (orders, escalation, retrieval).
"""

from functools import cache

from google.adk.tools import ToolContext

from novamart_agent import clock
from novamart_agent.config import DATA_DIR, INDEX_PATH, MIN_RETRIEVAL_SCORE, ORDERS_PATH, POLICY_DIR
from novamart_agent.retrieval import PolicyIndex
from novamart_agent.tools.escalation import GapLog, TicketStore
from novamart_agent.tools.orders import OrderService


@cache
def _index() -> PolicyIndex:
    from novamart_agent.embeddings import GeminiEmbedder

    embedder = GeminiEmbedder()
    return PolicyIndex.load_or_build(POLICY_DIR, INDEX_PATH, embedder, embedder_id=embedder.id)


@cache
def _orders() -> OrderService:
    return OrderService.from_file(ORDERS_PATH, today=clock.today)


def _tickets() -> TicketStore:
    return TicketStore(DATA_DIR / "tickets.jsonl")


def _gaps() -> GapLog:
    return GapLog(DATA_DIR / "gaps.jsonl")


def search_policies(query: str) -> dict:
    """Search NovaMart's official policy documents (returns, exchanges, warranty, price match,
    loyalty, shipping/click-and-collect, damaged goods & escalation).

    Always call this before stating any policy. Rephrase the employee's question as a focused
    policy query; call it more than once for questions that touch several topics.

    Args:
        query: A focused natural-language search query, e.g. "electronics return window".

    Returns:
        A dict with `results`: policy sections, each with a citable `chunk_id`, the section `text`,
        and a relevance `score`. An empty list means no policy covers the query.
    """
    hits = _index().search(query, k=4, min_score=MIN_RETRIEVAL_SCORE)
    return {
        "results": [
            {k: h[k] for k in ("chunk_id", "title", "section", "text", "last_updated", "score")} for h in hits
        ]
    }


def get_order_status(order_id: str) -> dict:
    """Look up a customer order in NovaMart's order system (live data).

    Args:
        order_id: The order number, e.g. "NM-1004".

    Returns:
        Order details: status, dates, items, prices, and pre-computed `days_since_delivery` /
        `business_days_late`. Use those numbers as-is; do not recompute dates yourself.
        If `found` is false, the order number is unknown.
    """
    return _orders().get_order_status(order_id)


def create_escalation_ticket(
    summary: str,
    category: str,
    urgency: str,
    cited_docs: list[str],
    tool_context: ToolContext,
    order_id: str | None = None,
) -> dict:
    """Open a ticket with the Operations team. Only call this after the employee has said yes.

    Args:
        summary: Self-contained handover for Ops: what the customer wants, the facts found
            (order status, amounts, dates), the policy checked, and what the employee already did.
        category: One of returns, shipping, pricing, loyalty, warranty, safety, loss_prevention, other.
        urgency: One of low, normal, high. Use high only for safety incidents or lost orders.
        cited_docs: The chunk_ids of the policy sections relevant to this case (may be empty).
        order_id: The related order number, if any.

    Returns:
        The created `ticket_id` and where it was routed, or an error to correct and retry.
    """
    return _tickets().create(
        summary=summary,
        category=category,
        urgency=urgency,
        store_id=tool_context.state.get("store_id", "unknown"),
        raised_by_role=tool_context.state.get("role"),
        order_id=order_id,
        cited_docs=cited_docs,
    )


def log_knowledge_gap(question: str, reason: str, tool_context: ToolContext) -> dict:
    """Record a NovaMart operational question that the policy documents could not answer, so the
    Operations team can fill the gap in the documentation. Call this every time you decline a
    NovaMart work question for lack of policy coverage. Do not call it for off-topic requests.

    Args:
        question: The employee's question, in their words.
        reason: Why it could not be answered, e.g. "no policy covers opened paint returns".
    """
    return _gaps().log(question=question, reason=reason, store_id=tool_context.state.get("store_id"))


ALL_TOOLS = [search_policies, get_order_status, create_escalation_ticket, log_knowledge_gap]
