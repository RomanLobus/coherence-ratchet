# ===== shop/order_total.py =====
"""Order total calculation."""
from shop.money import to_cents


def order_total(order):
    """Calculate the total for an order in cents."""
    total_cents = 0
    for line in order.get('lines', []):
        line_total = line['qty'] * line['price']
        total_cents += to_cents(line_total)
    return total_cents
