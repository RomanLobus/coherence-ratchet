"""Customer records."""


def display_name(customer):
    return f"{customer['first']} {customer['last']}"


def is_active(customer):
    return customer.get("status") == "active"
