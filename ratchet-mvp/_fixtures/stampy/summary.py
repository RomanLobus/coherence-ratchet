# Uses the whole order legitimately: the canonical shape lives here.
def order_summary(order):
    return {
        "id": order["id"],
        "customer": order["customer"],
        "lines": order["lines"],
        "total": order["total"],
        "status": order["status"],
    }
