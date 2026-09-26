"""Small, import-safe calculator helpers.

The functions in this module deliberately do not read input or print output, so
they can be reused from a command-line program as well as from other Python
code.
"""

from numbers import Number


def _validate_number(value: Number, name: str) -> None:
    """Raise a helpful error when an operand is not a number."""
    # ``bool`` is a Number subclass, but treating True as 1 is surprising in a
    # calculator and usually hides an input error.
    if isinstance(value, bool) or not isinstance(value, Number):
        raise TypeError(f"{name} must be a number")


def add(first: Number, second: Number) -> Number:
    """Return the sum of two numbers."""
    _validate_number(first, "first")
    _validate_number(second, "second")
    return first + second


def subtract(first: Number, second: Number) -> Number:
    """Return *second* subtracted from *first*."""
    _validate_number(first, "first")
    _validate_number(second, "second")
    return first - second


def multiply(first: Number, second: Number) -> Number:
    """Return the product of two numbers."""
    _validate_number(first, "first")
    _validate_number(second, "second")
    return first * second


def divide(first: Number, second: Number) -> Number:
    """Return *first* divided by *second*.

    Python's ``ZeroDivisionError`` is preserved so callers get the standard,
    predictable error for an undefined calculation.
    """
    _validate_number(first, "first")
    _validate_number(second, "second")
    return first / second


_OPERATIONS = {
    "+": add,
    "add": add,
    "-": subtract,
    "subtract": subtract,
    "*": multiply,
    "multiply": multiply,
    "/": divide,
    "divide": divide,
}


def calculate(first: Number, operation: str, second: Number) -> Number:
    """Apply an arithmetic *operation* to two operands.

    Both symbolic operators (``+``, ``-``, ``*``, ``/``) and their lower-case
    word forms are accepted.
    """
    if not isinstance(operation, str):
        raise TypeError("operation must be a string")

    try:
        calculator_operation = _OPERATIONS[operation.strip().lower()]
    except KeyError as error:
        raise ValueError(f"unsupported operation: {operation!r}") from error

    return calculator_operation(first, second)
