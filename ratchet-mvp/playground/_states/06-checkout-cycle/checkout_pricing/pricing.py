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
    from .checkout import current_promotion
    rate = current_promotion(customer)
    if rate is not None and not customer.get('trade_account'):
        return rate
    return Decimal('0')
