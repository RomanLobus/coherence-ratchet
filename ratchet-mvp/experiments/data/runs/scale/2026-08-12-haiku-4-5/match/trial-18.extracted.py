# ===== shop/order_total.py =====
"""Order totals."""
from shop.money import to_cents


def order_total(order):
    """Calculate the total for an order in cents."""
    total = 0
    for line in order['lines']:
        line_total = line['qty'] * line['price']
        total += to_cents(line_total)
    return total
