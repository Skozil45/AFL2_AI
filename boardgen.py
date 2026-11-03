"""Immutable board pattern shared safely by live states and search copies."""

# =============================================================================
# FILE: boardgen.py  -  the parts of the board that never change in a game.
#
# Calculated once, when the file is imported (the same for every game):
#   HOLES     - which cells are holes
#   PLAYABLE  - which cells can hold a disc
#   RAYS      - the straight lines from every cell (used to find captures)
# Calculated once per match, by create_board(seed):
#   Board     - the random "+n" / "-n" modifier of every tile
#
# -----------------------------------------------------------------------------
# CONCEPT: SEEDS
# -----------------------------------------------------------------------------
# A computer's "random" numbers come from a formula that starts from a
# number called the SEED. The same seed always gives the same numbers, so
# the same seed always gives the same board. That is why "Restart" and
# "Play Again" replay the exact same board.
#
# Who uses this file:
#   - engine.py: Board, HOLES, PLAYABLE, RAYS (the rules)
#   - ui/game_screen.py: create_board(seed) when a match starts
#   - ui/renderer.py: HOLES (holes are drawn differently)
# The Board is read-only, so the real game and the AI's copies can all
# share one Board safely.
# =============================================================================

# dataclass writes the __init__ method of Board for us.
from dataclasses import dataclass
# A random number generator that can be given a seed.
from random import Random
# The hole numbers and the range of n for modifiers.
from config import HOLE_NUMBERS, MODIFIER_MIN_N, MODIFIER_MAX_N
# All 91 cells and the neighbour table.
from hexgrid import CELLS, NEIGHBORS
# The modifier type and the function that turns it into points.
from modifiers import Modifier, tile_value

# The INDEX (number - 1) of every hole. A frozenset is a read-only set,
# which makes "i in HOLES" checks very fast.
HOLES = frozenset(n - 1 for n in HOLE_NUMBERS)
# The 72 indexes where a disc can be placed (every cell that is not a hole).
PLAYABLE = tuple(i for i in range(len(CELLS)) if i not in HOLES)


# Builds the RAYS table below.
# For every cell and each of the 6 directions, it lists the cells you pass
# when walking in a straight line, stopping before a hole or the edge.
# GameState.flips() walks these lists to find captures. Doing this once
# here is much faster than working out the lines on every move.
def _rays() -> tuple[tuple[tuple[int, ...], ...], ...]:
    """Precompute lines, ending before a hole or the board edge."""
    # The result: result[cell][direction] is a tuple of cell indexes.
    result = []
    # For each of the 91 cells...
    for i in range(len(CELLS)):
        # ...collect its 6 lines.
        directions = []
        # For each of the 6 directions...
        for direction in range(6):
            # ...collect the cells along that straight line.
            ray = []
            # Start with the cell right next to cell i.
            j = NEIGHBORS[i][direction]
            # Keep going until we leave the board (-1) or reach a hole.
            while j != -1 and j not in HOLES:
                ray.append(j)  # This cell is on the line.
                j = NEIGHBORS[j][direction]  # Take one more step the same way.
            # Save the finished line (a tuple, so it cannot be changed).
            directions.append(tuple(ray))
        # Save the 6 lines of cell i.
        result.append(tuple(directions))
    # Return the whole table as read-only tuples.
    return tuple(result)


# Calculated once, when this file is imported.
RAYS = _rays()


# One Board is created per match by create_board().
# frozen=True makes it read-only: its fields cannot change after creation.
@dataclass(frozen=True)
class Board:
    """The seed affects modifiers only; all other geometry is constant."""

    # The seed used to build this board (shown in the side panel).
    seed: int
    # For every cell: ("+", n) or ("-", n), or None for a hole.
    modifiers: tuple[Modifier | None, ...]
    # For every cell: its point value (0 for a hole).
    values: tuple[int, ...]


# Builds a new Board from a seed.
# Called by GameScreen.restart() (start, Restart, Play Again) and by
# engine.assert_opening().
def create_board(seed: int) -> Board:
    """Draw sign then magnitude in reading order, once per playable tile."""
    # A random generator of our own, started from the seed.
    rng = Random(seed)
    # For every cell in order: None for a hole, otherwise a random sign
    # followed by a random n from 1 to 5.
    modifiers = tuple(None if i in HOLES else
                      (rng.choice(("+", "-")), rng.randint(MODIFIER_MIN_N, MODIFIER_MAX_N))
                      for i in range(len(CELLS)))
    # Calculate every tile's value once, and pack everything into a Board.
    return Board(seed, modifiers, tuple(0 if m is None else tile_value(m) for m in modifiers))
