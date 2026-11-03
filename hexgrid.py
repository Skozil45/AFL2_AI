"""Pointy-top axial geometry; indices are reading-order numbers minus one."""

# =============================================================================
# FILE: hexgrid.py  -  hexagon maths only (no game rules, no Pygame).
#
# -----------------------------------------------------------------------------
# CONCEPT: AXIAL COORDINATES (q, r)
# -----------------------------------------------------------------------------
# A square grid uses (x, y). A hex grid can use two numbers too:
#   r = the ROW (-5 is the top row, 0 the middle row, +5 the bottom row)
#   q = the position along a slanted axis
#
# Here is the centre cell (0, 0) and its 6 neighbours:
#
#             (0,-1)  (1,-1)
#         (-1,0)  (0,0)  (1,0)
#             (-1,1)  (0,1)
#
# Moving right adds 1 to q. Moving down-left or down-right adds 1 to r.
# The 6 neighbour steps are listed in config.DIRECTIONS.
#
# Our board has radius 5, so a cell (q, r) exists when q, r and q + r are
# all between -5 and +5. That gives 91 cells.
#
# Every cell also has:
#   - an INDEX from 0 to 90 (its position in the CELLS list; used in code)
#   - a NUMBER from 1 to 91 (index + 1; shown to the player)
#
# -----------------------------------------------------------------------------
# CONCEPT: CUBE COORDINATES  (only needed for cube_round below)
# -----------------------------------------------------------------------------
# Adding a third value y = -q - r gives three numbers x, y, z with
# x + y + z = 0. This form makes rounding a mouse position to the nearest
# hex easy and exact.
#
# Who uses this file:
#   - boardgen.py: CELLS and NEIGHBORS (holes and capture lines)
#   - engine.py: CELLS (board size)
#   - ui/renderer.py: drawing the board and detecting clicks
# All the tables below are calculated ONCE, when the file is first imported.
# =============================================================================

# Trigonometry functions for pixel positions and hexagon corners.
from math import cos, sin, pi, sqrt
# The 6 neighbour steps and the board radius (5).
from config import DIRECTIONS, RADIUS

# TYPE ALIASES: short names for types, used only in type hints.
Cell = tuple[int, int]  # A cell (q, r).
Point = tuple[float, float]  # A screen position (x, y) in pixels.


# Returns the smallest and largest q that exist in row r.
# Used to build CELLS and ROW_STARTS below, and by cell_number().
# Example: the top row (r = -5) has q from 0 to 5.
def row_bounds(r: int) -> tuple[int, int]:
    """Inclusive q bounds of a valid row."""
    # Only rows -5 to +5 exist.
    if not -RADIUS <= r <= RADIUS:
        raise ValueError("Row outside board")
    # These come from the rules |q| <= 5 and |q + r| <= 5.
    return max(-RADIUS, -r - RADIUS), min(RADIUS, -r + RADIUS)


# All 91 cells in reading order: row by row from the top, left to right.
# A cell's position in this tuple IS its index (0 to 90).
CELLS: tuple[Cell, ...] = tuple(
    (q, r) for r in range(-RADIUS, RADIUS + 1)  # For every row r from -5 to 5...
    for q in range(row_bounds(r)[0], row_bounds(r)[1] + 1)  # ...every q in that row.
)
# The reverse lookup: from a cell (q, r) to its index.
# Example: INDEX[(0, -5)] is 0, the first cell.
INDEX = {cell: i for i, cell in enumerate(CELLS)}
# For each row r: the NUMBER (1-based) of the first cell in that row.
ROW_STARTS = {r: INDEX[(row_bounds(r)[0], r)] + 1 for r in range(-RADIUS, RADIUS + 1)}
# NEIGHBORS[i][d] is the index of cell i's neighbour in direction d,
# or -1 if that neighbour would be off the board.
NEIGHBORS = tuple(tuple(INDEX.get((q + dq, r + dr), -1) for dq, dr in DIRECTIONS)
                  for q, r in CELLS)


# Converts a cell (q, r) to the number (1 to 91) the player sees.
# It is the opposite of cell_from_number(). Useful for tests and debugging.
def cell_number(q: int, r: int) -> int:
    """Return the 1-based reading-order number, rejecting out-of-board cells."""
    # Reject cells that are not on the board.
    if (q, r) not in INDEX:
        raise ValueError("Cell outside board")
    # First number of the row, plus how far along the row the cell is.
    return ROW_STARTS[r] + q - row_bounds(r)[0]


# Converts a number (1 to 91) back to its cell (q, r).
def cell_from_number(n: int) -> Cell:
    """Inverse of cell_number."""
    # Only 1 to 91 are valid numbers.
    if not 1 <= n <= len(CELLS):
        raise ValueError("Cell number outside 1..91")
    # Number n is stored at index n - 1.
    return CELLS[n - 1]


# Returns the 6 coordinates around a cell, in config.DIRECTIONS order.
# They may be off the board; the game itself uses the NEIGHBORS table.
def neighbors(q: int, r: int) -> tuple[Cell, ...]:
    """Geometric neighbors in the specified six-direction order."""
    # Add each of the 6 steps to the cell.
    return tuple((q + dq, r + dr) for dq, dr in DIRECTIONS)


# How many steps apart two cells are. By default, the distance to the centre.
def distance(a: Cell, b: Cell = (0, 0)) -> int:
    """Hex distance in axial coordinates."""
    # The difference in q and in r.
    dq, dr = a[0] - b[0], a[1] - b[1]
    # The standard hex distance formula.
    return max(abs(dq), abs(dr), abs(dq + dr))


# Converts a cell to the pixel position of its centre on screen.
# size = the hex's radius in pixels; origin = where cell (0, 0) is drawn.
# Used by BoardRenderer when it is created.
def axial_to_pixel(q: int, r: int, size: float, origin: Point = (0, 0)) -> Point:
    """Map a cell center to screen coordinates."""
    # x: each row is shifted half a cell sideways (the r / 2 part).
    # y: rows are 1.5 hex sizes apart.
    return origin[0] + size * sqrt(3) * (q + r / 2), origin[1] + size * 1.5 * r


# A mouse position gives decimal coordinates like (1.3, -0.8).
# This function rounds them to the nearest real hex.
# Used by pixel_to_axial().
def cube_round(q: float, r: float) -> Cell:
    """Round fractional axial coordinates while preserving x+y+z=0."""
    # Convert to cube coordinates: x = q, z = r, y = -q - r.
    x, z, y = q, r, -q - r
    # Round each of the three values to a whole number.
    rx, ry, rz = round(x), round(y), round(z)
    # How much each value changed because of rounding.
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    # Rounding can break x + y + z = 0. To fix it, recalculate the value
    # that changed the most from the other two.
    if dx > dy and dx > dz:  # x changed the most...
        rx = -ry - rz  # ...so recalculate x.
    elif dy > dz:  # y changed the most...
        ry = -rx - rz  # ...so recalculate y.
    else:  # z changed the most...
        rz = -rx - ry  # ...so recalculate z.
    # Back to axial coordinates: q = x, r = z.
    return rx, rz


# Converts a pixel position (for example, the mouse) to the cell under it.
# It is the opposite of axial_to_pixel(), followed by rounding.
# Used by BoardRenderer.hit_test().
def pixel_to_axial(x: float, y: float, size: float, origin: Point = (0, 0)) -> Cell:
    """Inverse transform with cube rounding for hit testing."""
    # Measure from cell (0, 0), in units of one hex size.
    x, y = (x - origin[0]) / size, (y - origin[1]) / size
    # Undo the axial_to_pixel formula, then round to the nearest hex.
    return cube_round(sqrt(3) * x / 3 - y / 3, 2 * y / 3)


# Returns the 6 corner points of a hexagon, used to draw its outline.
def corners(center: Point, size: float) -> list[Point]:
    """Six vertices of a pointy-top hexagon."""
    # One corner every 60 degrees (pi / 3). Starting at -30 degrees (-pi / 6)
    # puts a corner at the top, which makes the hexagon "pointy-top".
    return [(center[0] + size * cos(pi / 3 * k - pi / 6),
             center[1] + size * sin(pi / 3 * k - pi / 6)) for k in range(6)]
