"""The two supported operators act on a tile's base value only."""

from operator import add, sub
from collections.abc import Callable
from config import BASE_VALUE, MODIFIER_MIN_N, MODIFIER_MAX_N

Modifier = tuple[str, int]
OPERATORS: dict[str, Callable[[int, int], int]] = {"+": add, "-": sub}


def tile_value(modifier: Modifier) -> int:
    """Validate a modifier and compute its immutable tile value."""
    sign, n = modifier
    if sign not in OPERATORS or type(n) is not int or not MODIFIER_MIN_N <= n <= MODIFIER_MAX_N:
        raise ValueError("Expected + or - and an integer in 1..5")
    return OPERATORS[sign](BASE_VALUE, n)
