# The good design (control): take only what is needed, no entity passed.
def lookup_order(order_id):
    return fetch(order_id)

def fetch(i): ...
