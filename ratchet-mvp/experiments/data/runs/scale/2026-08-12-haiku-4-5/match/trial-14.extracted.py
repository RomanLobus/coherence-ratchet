# ===== shop/order_total.py =====
"""Order total calculations."""
from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate the order total as an integer number of cents.
    
    Sums the order lines where each line has qty and price.
    Price is a decimal amount in currency units, not cents.
    """
    total_cents = 0
    for line in order.get('lines', []):
        qty = line['qty']
        price = Decimal(str(line['price']))
        line_total_cents = int((qty * price * 100).to_integral_value(rounding=ROUND_HALF_UP))
        total_cents += line_total_cents
    return total_cents
