# ===== shop/order_total.py =====
"""Order totals."""

from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate the order's total as an integer number of cents.
    
    Sums all lines where each line has 'qty' and 'price' (in currency units).
    Returns the total as an integer number of cents.
    """
    total = Decimal('0')
    for line in order['lines']:
        qty = Decimal(str(line['qty']))
        price = Decimal(str(line['price']))
        total += qty * price
    
    return int((total * 100).to_integral_value(rounding=ROUND_HALF_UP))
