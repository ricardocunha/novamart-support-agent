"""Mock order-status API. Stands in for NovaMart's real order management system."""

import json
from collections.abc import Callable
from datetime import date, timedelta
from pathlib import Path


def _business_days_between(start: date, end: date) -> int:
    """Weekdays strictly after `start`, up to and including `end`."""
    days, d = 0, start
    while d < end:
        d += timedelta(days=1)
        if d.weekday() < 5:
            days += 1
    return days


class OrderService:
    def __init__(self, orders: list[dict], today: Callable[[], date]):
        self._orders = {o["order_id"].upper(): o for o in orders}
        self._today = today

    @classmethod
    def from_file(cls, path: str | Path, today: Callable[[], date]) -> OrderService:
        return cls(json.loads(Path(path).read_text()), today)

    def get_order_status(self, order_id: str) -> dict:
        key = order_id.strip().upper()
        order = self._orders.get(key)
        if order is None:
            return {
                "found": False,
                "error": "ORDER_NOT_FOUND",
                "order_id": key,
                "message": f"No order with id {key}. Ask the employee to double-check the order number.",
            }

        today = self._today()
        result = {"found": True, "as_of": today.isoformat(), **order}
        # Pre-compute date facts so the LLM never does date arithmetic.
        if order.get("delivered_on"):
            result["days_since_delivery"] = (today - date.fromisoformat(order["delivered_on"])).days
        if order["status"] == "in_transit" and order.get("estimated_delivery"):
            result["business_days_late"] = _business_days_between(
                date.fromisoformat(order["estimated_delivery"]), today
            )
        return result
