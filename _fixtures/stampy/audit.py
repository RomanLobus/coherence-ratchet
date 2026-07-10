# Stamp coupling: receives the whole order, uses only one field.
def log_order(order):
    record(order["id"])

# Stamp coupling: receives the whole order and forwards it wholesale, using nothing.
def archive(order):
    store(order)

def record(x): ...
def store(x): ...
