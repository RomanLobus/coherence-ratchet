# ===== shop/order_total.py =====
"""Order totals."""
from decimal import Decimal, ROUND_HALF_UP
from shop.settle import to_minor_units


def order_total(order):
    """Calculate the total cost of an order in cents."""
    total = Decimal('0')
    for line in order['lines']:
        line_total = Decimal(str(line['qty'])) * Decimal(str(line['price']))
        total += line_total
    return to_minor_units(total)
