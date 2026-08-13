from decimal import Decimal, ROUND_HALF_UP

from .pricing import unit_price

CAMPAIGNS = {
    'relaunch-june': Decimal('0.07'),
}


def build_order(customer, cart):
    line_items = []
    for entry in cart:
        line_items.append({
            'sku': entry['sku'],
            'unit_price': unit_price(entry['list_price'], customer.get('tier')),
            'quantity': entry['count'],
        })
    return {
        'line_items': line_items,
        'customer': customer['id'],
        'status': 'PENDING',
        'total': None,
    }


def compute_order_total(order):
    total = Decimal('0')
    for item in order['line_items']:
        total += Decimal(str(item['unit_price'])) * item['quantity']
    return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def finalize_order(order):
    order['total'] = compute_order_total(order)
    if order['total'] < Decimal('0'):
        raise ValueError('order total cannot be negative')
    return order


def settle_order(order, payment_ref):
    if order['status'] != 'PENDING':
        raise ValueError('only a pending order can be settled')
    order['status'] = 'SETTLED'
    order['payment_ref'] = payment_ref
    return order


def cancel_order(order, reason):
    order['status'] = 'CANCELLED'
    order['cancel_reason'] = reason or 'customer request'
    order['total'] = Decimal('0')
    return order


def loyalty_discount(order, customer):
    if not customer.get('loyalty_member'):
        return Decimal('0')
    total = order['total'] if order['total'] is not None else compute_order_total(order)
    return (total * Decimal('0.15')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def current_promotion(customer):
    campaign = customer.get('campaign')
    if campaign not in CAMPAIGNS:
        return None
    if customer.get('campaign_opt_out'):
        return None
    return CAMPAIGNS[campaign]


def order_reference(order, placed_on):
    day = placed_on.strftime('%Y%m%d')
    return 'ORD-{}-{}'.format(day, order['customer'])
