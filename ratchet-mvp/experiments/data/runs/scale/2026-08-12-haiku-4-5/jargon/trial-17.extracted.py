# ===== shop/order_total.py =====
"""Order total calculation."""

from decimal import Decimal, ROUND_HALF_UP


def order_total(order):
    """Calculate the total cost of an order in cents.
    
    Sums all line items where each line has qty and price.
    Price is in currency units (e.g., dollars), converted to cents.
    """
    total_cents = 0
    for line in order['lines']:
        qty = line['qty']
        price = Decimal(str(line['price']))
        line_total_cents = int((price * qty * 100).to_integral_value(rounding=ROUND_HALF_UP))
        total_cents += line_total_cents
    return total_cents
