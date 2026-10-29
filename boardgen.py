"""Immutable board pattern shared safely by live states and search copies."""

from dataclasses import dataclass
from random import Random
from config import HOLE_NUMBERS, MODIFIER_MIN_N, MODIFIER_MAX_N
from hexgrid import CELLS, NEIGHBORS
from modifiers import Modifier, tile_value

HOLES = frozenset(n - 1 for n in HOLE_NUMBERS)
PLAYABLE = tuple(i for i in range(len(CELLS)) if i not in HOLES)


def _rays() -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Precompute lines, ending before a hole or the board edge."""
    result = []
    for i in range(len(CELLS)):
        directions = []
        for direction in range(6):
            ray = []
            j = NEIGHBORS[i][direction]
            while j != -1 and j not in HOLES:
                ray.append(j)
                j = NEIGHBORS[j][direction]
            directions.append(tuple(ray))
        result.append(tuple(directions))
    return tuple(result)


RAYS = _rays()


@dataclass(frozen=True)
class Board:
    """The seed affects modifiers only; all other geometry is constant."""

    seed: int
    modifiers: tuple[Modifier | None, ...]
    values: tuple[int, ...]


def create_board(seed: int) -> Board:
    """Draw sign then magnitude in reading order, once per playable tile."""
    rng = Random(seed)
    modifiers = tuple(None if i in HOLES else
                      (rng.choice(("+", "-")), rng.randint(MODIFIER_MIN_N, MODIFIER_MAX_N))
                      for i in range(len(CELLS)))
    return Board(seed, modifiers, tuple(0 if m is None else tile_value(m) for m in modifiers))
