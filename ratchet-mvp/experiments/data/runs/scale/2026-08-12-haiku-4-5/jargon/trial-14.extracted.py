# ===== shop/order_total.py =====
"""Order total calculation."""
from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate the total of an order as an integer number of cents."""
    total = Decimal('0')
    for line in order['lines']:
        line_total = Decimal(str(line['qty'])) * Decimal(str(line['price']))
        total += line_total
    return int((total * 100).to_integral_value(rounding=ROUND_HALF_UP))
