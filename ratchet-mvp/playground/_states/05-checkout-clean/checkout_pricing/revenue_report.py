from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP

from .pricing import tax_on


def as_minor_units(amount):
    value = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    return int(value * 100)


def report_total(order):
    amount = Decimal('0')
    for line in order['lines']:
        amount += Decimal(str(line['net'])) * line['qty']
    return amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def net_of_tax(order):
    gross = report_total(order)
    gst = tax_on(gross)
    return gross - gst


def settled_orders(orders):
    settled = []
    for order in orders:
        if order.get('stage') == 'SETTLED':
            settled.append(order)
    return settled


def daily_totals(orders):
    by_day = {}
    for order in settled_orders(orders):
        day = order['booked_on']
        by_day[day] = by_day.get(day, Decimal('0')) + report_total(order)
    return by_day


def tier_summary(orders):
    summary = {}
    for order in settled_orders(orders):
        segment = order.get('segment') or 'BASE'
        summary[segment] = summary.get(segment, 0) + 1
    return summary


def revenue_line(order):
    cents = as_minor_units(report_total(order))
    return '{},{},{}'.format(order['booked_on'], order['ref'], cents)


def export_csv(orders):
    rows = ['booked_on,reference,cents']
    for order in settled_orders(orders):
        rows.append(revenue_line(order))
    return '\n'.join(rows)
