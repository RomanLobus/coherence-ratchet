"""Pure and higher-order functions used to establish the CrossHair boundary.

The integer input represents thousandths of a currency unit. Converting it to
hundredths creates an exact tie whenever the final digit is five.
"""


def round_half_up(amount_thousandths: int) -> int:
    quotient, remainder = divmod(amount_thousandths, 10)
    return quotient + (1 if remainder >= 5 else 0)


def round_half_even(amount_thousandths: int) -> int:
    quotient, remainder = divmod(amount_thousandths, 10)
    increment = remainder > 5 or (remainder == 5 and quotient % 2 != 0)
    return quotient + (1 if increment else 0)


class TransientError(Exception):
    pass


def retry_original(operation, attempts: int = 4):
    error = None
    for _ in range(attempts):
        try:
            return operation()
        except TransientError as caught:
            error = caught
    raise error


def retry_mutation(operation, attempts: int = 3):
    error = None
    for _ in range(attempts):
        try:
            return operation()
        except Exception as caught:
            error = caught
    raise error
