from copy import deepcopy
from decimal import Decimal, InvalidOperation


def _to_non_negative_int(value, field_name):
    if isinstance(value, bool) or value is None:
        raise ValueError(f"{field_name} must be a non-negative integer")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{field_name} must be a non-negative integer")

    if number != number.to_integral_value() or number < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")

    return int(number)


def build_order(customer_id, items):
    """
    Build a customer order dictionary from a customer id and line items.

    Args:
        customer_id: Identifier for the customer.
        items: List of dictionaries, each containing:
            - product_id
            - quantity
            - unit_price_cents

    Returns:
        dict: {
            "customer_id": customer_id,
            "items": [...],
            "total_cents": int
        }

    Raises:
        ValueError: If items are malformed or numeric values are invalid.
        TypeError: If items is not a list or an item is not a dictionary.
    """
    if not isinstance(items, list):
        raise TypeError("items must be a list")

    normalized_items = []
    total_cents = 0

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            raise TypeError(f"item at index {index} must be a dictionary")

        if "product_id" not in item:
            raise ValueError(f"item at index {index} is missing 'product_id'")
        if "quantity" not in item:
            raise ValueError(f"item at index {index} is missing 'quantity'")
        if "unit_price_cents" not in item:
            raise ValueError(f"item at index {index} is missing 'unit_price_cents'")

        product_id = deepcopy(item["product_id"])
        quantity = _to_non_negative_int(item["quantity"], f"item[{index}].quantity")
        unit_price_cents = _to_non_negative_int(
            item["unit_price_cents"], f"item[{index}].unit_price_cents"
        )

        line_total_cents = quantity * unit_price_cents
        total_cents += line_total_cents

        normalized_items.append(
            {
                "product_id": product_id,
                "quantity": quantity,
                "unit_price_cents": unit_price_cents,
                "line_total_cents": line_total_cents,
            }
        )

    return {
        "customer_id": deepcopy(customer_id),
        "items": normalized_items,
        "total_cents": total_cents,
    }
