from datetime import date

from novamart_agent.tools.orders import OrderService

TODAY = date(2026, 11, 3)  # Tuesday


def svc():
    return OrderService.from_file("data/orders.json", today=lambda: TODAY)


def test_known_order_returns_status_and_items():
    result = svc().get_order_status("NM-1001")
    assert result["found"] is True
    assert result["status"] == "delivered"
    assert result["items"][0]["name"] == "TrailRunner shoes"


def test_delivered_order_reports_days_since_delivery():
    # delivered 2026-10-20 -> 14 calendar days before 2026-11-03
    assert svc().get_order_status("NM-1001")["days_since_delivery"] == 14


def test_late_in_transit_order_reports_business_days_late():
    # estimated 2026-10-27 (Tue); business days after it up to 2026-11-03: Oct 28,29,30, Nov 2,3 = 5
    result = svc().get_order_status("NM-1004")
    assert result["business_days_late"] == 5


def test_on_time_order_is_not_late():
    assert svc().get_order_status("NM-1003")["business_days_late"] == 0


def test_lookup_is_case_and_whitespace_insensitive():
    assert svc().get_order_status("  nm-1001 ")["found"] is True


def test_unknown_order_returns_typed_not_found():
    result = svc().get_order_status("NM-9999")
    assert result == {
        "found": False,
        "error": "ORDER_NOT_FOUND",
        "order_id": "NM-9999",
        "message": "No order with id NM-9999. Ask the employee to double-check the order number.",
    }
