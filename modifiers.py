"""The two supported operators act on a tile's base value only."""

# =============================================================================
# FILE: modifiers.py  -  turns a tile's modifier into its point value.
#
# Every playable tile has a modifier: a sign ("+" or "-") and a number n
# from 1 to 5. The tile is worth BASE_VALUE (1) changed by that modifier:
#     ("+", 3)  ->  1 + 3 =  4 points
#     ("-", 2)  ->  1 - 2 = -1 point
#
# Used by boardgen.create_board(), which calls tile_value() once for every
# playable tile when a board is built.
# =============================================================================

# add(a, b) does a + b, and sub(a, b) does a - b, as normal functions.
from operator import add, sub
# Callable is only used in a type hint below (it means "a function").
from collections.abc import Callable
# The base value (1) and the allowed range of n (1 to 5).
from config import BASE_VALUE, MODIFIER_MIN_N, MODIFIER_MAX_N

# Type alias: a modifier is (sign, n), for example ("+", 3).
Modifier = tuple[str, int]
# Connects each sign to the function that applies it.
# OPERATORS["+"] is the add function and OPERATORS["-"] is sub.
OPERATORS: dict[str, Callable[[int, int], int]] = {"+": add, "-": sub}


# Checks a modifier and returns the tile's point value.
# Called by boardgen.create_board() once per playable tile.
def tile_value(modifier: Modifier) -> int:
    """Validate a modifier and compute its immutable tile value."""
    # Split the pair, for example ("+", 3) into sign = "+" and n = 3.
    sign, n = modifier
    # The sign must be + or -, and n must be a whole number from 1 to 5.
    if sign not in OPERATORS or type(n) is not int or not MODIFIER_MIN_N <= n <= MODIFIER_MAX_N:
        raise ValueError("Expected + or - and an integer in 1..5")
    # Look up the function and apply it, for example add(1, 3) = 4.
    return OPERATORS[sign](BASE_VALUE, n)
