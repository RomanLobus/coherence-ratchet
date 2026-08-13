# ===== shop/order_total.py =====
"""Order total calculation."""
from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate order total as an integer number of cents."""
    total = Decimal('0')
    for line in order['lines']:
        qty = Decimal(str(line['qty']))
        price = Decimal(str(line['price']))
        total += qty * price
    return int((total * 100).to_integral_value(rounding=ROUND_HALF_UP))
