# ===== shop/order_total.py =====
"""Order total calculation."""

from shop.money import to_cents


def order_total(order):
    """Calculate the total cost of an order in cents.
    
    Sums the line items where each line has qty and price (in currency units).
    Returns the total as an integer number of cents.
    """
    total_cents = 0
    for line in order.get('lines', []):
        line_total = line['qty'] * line['price']
        total_cents += to_cents(line_total)
    return total_cents
