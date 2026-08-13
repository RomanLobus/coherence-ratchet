"""Pricing producer: integer milli-cents with explicit half-up rounding."""


def half_up(milli_cents: int) -> int:
    if milli_cents < 0:
        raise ValueError("milli_cents must be non-negative")
    return (milli_cents + 5) // 10


def price_response(order_id: str, subtotal_milli: int, discount_bps: int = 0) -> dict:
    if not 0 <= discount_bps <= 10000:
        raise ValueError("discount_bps must be between 0 and 10000")
    discounted = subtotal_milli * (10000 - discount_bps) // 10000
    return {"order_id": order_id, "total_cents": half_up(discounted), "currency": "USD"}

