"""The checkout-pricing fixture, in two states.

A small retail pricing seam: checkout builds orders, pricing owns rates and
rounding, receipt renders what the customer sees, and the revenue report
recomputes everything for finance. The decay is already in place — three
independent implementations of "total an order", two minor-unit converters,
and four literals (the GOLD rate, the rounding quantum, two status strings)
that several modules agree on without saying so.

Two states differ by exactly one thing: in `06-checkout-cycle` a deadline
change makes pricing reach back into checkout for the campaign schedule (a
function-level import, the classic cycle-hiding move), closing the
checkout <-> pricing dependency cycle. Everything else is byte-identical.

Each state is the full source tree. `materialize()` writes a state to a
directory; the metric engine measures it. Nothing here is AI-generated at
run time — the decay is scripted so the demo is reproducible.
"""

from __future__ import annotations

import os

# --- pricing: the module everyone leans on -----------------------------------

PRICING_CLEAN = '''\
from decimal import Decimal, ROUND_HALF_EVEN, ROUND_HALF_UP

TIER_RATES = {
    'GOLD': Decimal('0.15'),
    'SILVER': Decimal('0.08'),
    'MEMBER': Decimal('0.03'),
}

GST_RATE = Decimal('0.09')

PROMO_RATES = {
    'relaunch': Decimal('0.05'),
    'clearance': Decimal('0.12'),
}


def to_minor_units(amount):
    quantised = Decimal(str(amount)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return int(quantised * 100)


def rate_for_tier(tier):
    rate = TIER_RATES.get(tier)
    if rate is None:
        return Decimal('0')
    return rate


def unit_price(list_price, tier):
    base = Decimal(str(list_price))
    discount = base * rate_for_tier(tier)
    return (base - discount).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def extended_price(list_price, quantity, tier):
    each = unit_price(list_price, tier)
    return (each * quantity).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def tax_on(net_amount):
    gst = net_amount * GST_RATE
    return gst.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def round_amount(value, channel):
    if channel == 'kiosk':
        return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_EVEN)
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def bulk_rate(quantity):
    if quantity >= 24:
        return Decimal('0.06')
    if quantity >= 12:
        return Decimal('0.04')
    return Decimal('0')


def promotional_rate(customer):
    rate = PROMO_RATES.get(customer.get('promo'))
    if rate is not None and not customer.get('trade_account'):
        return rate
    return Decimal('0')
'''

# 06 only: promotional_rate now reads the campaign schedule out of checkout.
# The import is inside the function because the top-level version breaks the
# interpreter — the cycle is still there, it is just harder to see.

PRICING_CYCLE = PRICING_CLEAN.replace(
    '''\
def promotional_rate(customer):
    rate = PROMO_RATES.get(customer.get('promo'))
    if rate is not None and not customer.get('trade_account'):
        return rate
    return Decimal('0')
''',
    '''\
def promotional_rate(customer):
    from .checkout import current_promotion
    rate = current_promotion(customer)
    if rate is not None and not customer.get('trade_account'):
        return rate
    return Decimal('0')
''',
)

# --- checkout: builds and settles orders --------------------------------------

CHECKOUT = '''\
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
'''

# --- receipt: what the customer sees ------------------------------------------

RECEIPT = '''\
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
    return '\\n'.join(body)


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
'''

# --- revenue report: finance recomputes everything -----------------------------

REVENUE_REPORT = '''\
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
    return '\\n'.join(rows)
'''

# --- the two states -----------------------------------------------------------

CLEAN = {
    "checkout_pricing/pricing.py": PRICING_CLEAN,
    "checkout_pricing/checkout.py": CHECKOUT,
    "checkout_pricing/receipt.py": RECEIPT,
    "checkout_pricing/revenue_report.py": REVENUE_REPORT,
}

CYCLE = dict(CLEAN)
CYCLE["checkout_pricing/pricing.py"] = PRICING_CYCLE

STATES = [
    ("05-checkout-clean", "the decayed baseline: duplication and shared literals, no cycle", CLEAN),
    ("06-checkout-cycle", "pricing reaches back into checkout: the dependency cycle closes", CYCLE),
]


def materialize(files: dict, dest: str) -> str:
    for rel, src in files.items():
        path = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(src)
    return dest
