from copy import deepcopy
from typing import Any, Dict, List


def build_order(customer_id: Any, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a customer order dictionary from the given customer id and items.

    Args:
        customer_id: Identifier for the customer.
        items: A list of dictionaries, each containing:
            - product_id
            - quantity
            - unit_price_cents

    Returns:
        A dictionary with:
            - customer_id
            - items
            - total_cents
    """
    line_items = deepcopy(items)
    total_cents = sum(
        item["quantity"] * item["unit_price_cents"] for item in line_items
    )

    return {
        "customer_id": customer_id,
        "items": line_items,
        "total_cents": total_cents,
    }
