# ===== shop/order_total.py =====
"""Order totals."""
from shop.settle import to_minor_units


def order_total(order):
    """Calculate the total of an order in minor units (cents)."""
    total = 0
    for line in order['lines']:
        line_total = line['qty'] * line['price']
        total += to_minor_units(line_total)
    return total
