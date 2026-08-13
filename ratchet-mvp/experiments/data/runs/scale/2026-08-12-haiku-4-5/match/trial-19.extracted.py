# ===== shop/order_total.py =====
"""Order total calculation."""

from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate the order's total as an integer number of cents.
    
    Sums order['lines'] where each line has qty and price.
    Price is a decimal amount in currency units, not cents.
    """
    total_cents = 0
    for line in order.get('lines', []):
        qty = line.get('qty', 0)
        price = line.get('price', 0)
        line_total = Decimal(str(qty)) * Decimal(str(price))
        line_cents = int((line_total * 100).to_integral_value(rounding=ROUND_HALF_UP))
        total_cents += line_cents
    return total_cents
