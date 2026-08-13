from decimal import Decimal

from .pricing import to_minor_units


def receipt_total_cents(order):
    total_cents = Decimal('0')
    for item in order['items']:
        total_cents += Decimal(str(item['price'])) * item['qty']
    return int(total_cents * 100)


def format_money(amount):
    cents = to_minor_units(amount)
    return '{}.{:02d}'.format(cents // 100, cents % 100)


def format_line(item):
    label = item.get('label') or item['sku']
    money = format_money(item['price'])
    return '{:<20} x{:>3}  {:>10}'.format(label, item['qty'], money)


def receipt_header(order):
    issued = order['issued_at'].strftime('%d %b %Y')
    return f"RECEIPT {order['reference']}  {issued}"


def render_receipt(order):
    body = [receipt_header(order)]
    for item in order['items']:
        body.append(format_line(item))
    cents = receipt_total_cents(order)
    body.append('TOTAL {}.{:02d}'.format(cents // 100, cents % 100))
    return '\n'.join(body)


def payment_status_label(order):
    if order.get('state') == 'PENDING':
        return 'PAYMENT PENDING'
    if order.get('state') == 'REFUNDED':
        return 'REFUNDED IN FULL'
    return 'PAID'


def gst_breakdown(order):
    total_cents = receipt_total_cents(order)
    gst_cents = total_cents * 9 // 109
    return {'net_cents': total_cents - gst_cents, 'gst_cents': gst_cents}
