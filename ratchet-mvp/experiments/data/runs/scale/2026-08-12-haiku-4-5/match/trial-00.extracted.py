# ===== shop/order_total.py =====
"""Order total calculation."""

from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate the order's total as an integer number of cents.
    
    Sums all lines in the order where each line has qty and price.
    Price is expected to be a decimal amount in currency units, not cents.
    """
    total_cents = 0
    for line in order.get('lines', []):
        qty = line['qty']
        price = Decimal(str(line['price']))
        line_total = (qty * price * 100).to_integral_value(rounding=ROUND_HALF_UP)
        total_cents += int(line_total)
    return total_cents
