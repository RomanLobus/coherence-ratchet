"""Known semantic mutation: the contract shape is unchanged but half-cent behaviour differs."""


def half_even(milli_cents: int) -> int:
    if milli_cents < 0:
        raise ValueError("milli_cents must be non-negative")
    whole, remainder = divmod(milli_cents, 10)
    if remainder > 5 or (remainder == 5 and whole % 2 == 1):
        return whole + 1
    return whole


def price_response(order_id: str, subtotal_milli: int, discount_bps: int = 0) -> dict:
    if not 0 <= discount_bps <= 10000:
        raise ValueError("discount_bps must be between 0 and 10000")
    discounted = subtotal_milli * (10000 - discount_bps) // 10000
    return {"order_id": order_id, "total_cents": half_even(discounted), "currency": "USD"}

