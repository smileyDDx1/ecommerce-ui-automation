"""Price parsing and the order maths the checkout overview is checked against."""

import re
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable

_AMOUNT = re.compile(r"\$(\d+(?:\.\d{1,2})?)")
CENT = Decimal("0.01")


def parse_amount(text: str) -> Decimal:
    """Pull the dollar amount out of text such as '$29.99' or 'Item total: $29.99'."""
    match = _AMOUNT.search(text)
    if not match:
        raise ValueError(f"No dollar amount in {text!r}")
    return Decimal(match.group(1))


def format_amount(amount: Decimal) -> str:
    return f"${amount.quantize(CENT)}"


def order_totals(prices: Iterable[Decimal], tax_rate: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Return (subtotal, tax, total) for the given item prices, tax rounded to the cent."""
    subtotal = sum(prices, Decimal("0"))
    tax = (subtotal * tax_rate).quantize(CENT, rounding=ROUND_HALF_UP)
    return subtotal, tax, subtotal + tax
