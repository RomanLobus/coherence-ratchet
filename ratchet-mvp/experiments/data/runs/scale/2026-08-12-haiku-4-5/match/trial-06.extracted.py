# ===== shop/order_total.py =====
"""Order total calculations."""
from shop.money import to_cents


def order_total(order):
    """Calculate the order total as an integer number of cents."""
    total_cents = 0
    for line in order['lines']:
        line_total = line['qty'] * line['price']
        total_cents += to_cents(line_total)
    return total_cents
