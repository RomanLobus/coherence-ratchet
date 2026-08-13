# ===== shop/order_total.py =====
"""Order totals."""
from shop.settle import to_minor_units


def order_total(order):
    """Calculate the order's total as an integer number of cents."""
    total = sum(line['qty'] * line['price'] for line in order['lines'])
    return to_minor_units(total)
