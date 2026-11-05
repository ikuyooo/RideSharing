"""Exact money arithmetic for the pricing module (P3 design decision DD-P3-01).

Every intermediate value is an exact rational (`fractions.Fraction`); no binary float ever
takes part in a VND computation. Inputs that arrive as floats (OSRM metres / seconds, YAML
rates such as 0.85) are converted through their shortest decimal representation, so 0.85
becomes exactly 17/20 and 2400.3 s exactly 24003/10.

Amounts that are paid or charged are integer VND (D-48: 1 base unit = 1 VND). They are
produced only by `floor_step` (the 1.000 VND rounding of D-18) or by `exact_vnd`, which
refuses a non-integer amount instead of rounding it silently.
"""

from decimal import ROUND_HALF_EVEN, Decimal
from fractions import Fraction

Money = Fraction


class NonIntegralAmount(ArithmeticError):
    """A payable amount is not a whole number of VND (the configuration would need a rounding rule)."""


def q(value: int | float | str | Decimal | Fraction) -> Fraction:
    """Exact rational of a number; floats go through their shortest decimal repr."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool):
        raise TypeError("bool is not a number here")
    if isinstance(value, float):
        return Fraction(Decimal(repr(value)))
    return Fraction(value)


def floor_step(amount: Fraction, step: int) -> int:
    """floor(amount / step) x step - the 1.000 VND rounding of D-18 (never rounds up)."""
    return int(amount // step) * step


def exact_vnd(amount: Fraction) -> int:
    if amount.denominator != 1:
        raise NonIntegralAmount(f"{amount} VND is not a whole number of VND")
    return int(amount)


def to_numeric_2(value: Fraction) -> Decimal:
    """Storage form of an exact amount in a NUMERIC(.., 2) column (half-even to 0.01 VND)."""
    return (Decimal(value.numerator) / Decimal(value.denominator)).quantize(Decimal("0.01"), ROUND_HALF_EVEN)


def to_rational_text(value: Fraction) -> str:
    """Loss-free storage form ("num/den") next to the NUMERIC column."""
    return f"{value.numerator}/{value.denominator}"


def from_rational_text(text: str) -> Fraction:
    return Fraction(text)
