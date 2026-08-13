# ===== shop/order_total.py =====
"""Order total calculation."""
from shop.money import to_cents


def order_total(order):
    """Calculate the order's total as an integer number of cents."""
    total = 0
    for line in order['lines']:
        line_total = line['qty'] * line['price']
        total += to_cents(line_total)
    return total
