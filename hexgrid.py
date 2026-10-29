"""Pointy-top axial geometry; indices are reading-order numbers minus one."""

from math import cos, sin, pi, sqrt
from config import DIRECTIONS, RADIUS

Cell = tuple[int, int]
Point = tuple[float, float]


def row_bounds(r: int) -> tuple[int, int]:
    """Inclusive q bounds of a valid row."""
    if not -RADIUS <= r <= RADIUS:
        raise ValueError("Row outside board")
    return max(-RADIUS, -r - RADIUS), min(RADIUS, -r + RADIUS)


CELLS: tuple[Cell, ...] = tuple(
    (q, r) for r in range(-RADIUS, RADIUS + 1)
    for q in range(row_bounds(r)[0], row_bounds(r)[1] + 1)
)
INDEX = {cell: i for i, cell in enumerate(CELLS)}
ROW_STARTS = {r: next(i + 1 for i, cell in enumerate(CELLS) if cell[1] == r)
              for r in range(-RADIUS, RADIUS + 1)}
NEIGHBORS = tuple(tuple(INDEX.get((q + dq, r + dr), -1) for dq, dr in DIRECTIONS)
                  for q, r in CELLS)


def cell_number(q: int, r: int) -> int:
    """Return the 1-based reading-order number, rejecting out-of-board cells."""
    if (q, r) not in INDEX:
        raise ValueError("Cell outside board")
    return ROW_STARTS[r] + q - row_bounds(r)[0]


def cell_from_number(n: int) -> Cell:
    """Inverse of cell_number."""
    if not 1 <= n <= len(CELLS):
        raise ValueError("Cell number outside 1..91")
    return CELLS[n - 1]


def neighbors(q: int, r: int) -> tuple[Cell, ...]:
    """Geometric neighbors in the specified six-direction order."""
    return tuple((q + dq, r + dr) for dq, dr in DIRECTIONS)


def distance(a: Cell, b: Cell = (0, 0)) -> int:
    """Hex distance in axial coordinates."""
    dq, dr = a[0] - b[0], a[1] - b[1]
    return max(abs(dq), abs(dr), abs(dq + dr))


def axial_to_pixel(q: int, r: int, size: float, origin: Point = (0, 0)) -> Point:
    """Map a cell center to screen coordinates."""
    return origin[0] + size * sqrt(3) * (q + r / 2), origin[1] + size * 1.5 * r


def cube_round(q: float, r: float) -> Cell:
    """Round fractional axial coordinates while preserving x+y+z=0."""
    x, z, y = q, r, -q - r
    rx, ry, rz = round(x), round(y), round(z)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    else:
        rz = -rx - ry
    return rx, rz


def pixel_to_axial(x: float, y: float, size: float, origin: Point = (0, 0)) -> Cell:
    """Inverse transform with cube rounding for hit testing."""
    x, y = (x - origin[0]) / size, (y - origin[1]) / size
    return cube_round(sqrt(3) * x / 3 - y / 3, 2 * y / 3)


def corners(center: Point, size: float) -> list[Point]:
    """Six vertices of a pointy-top hexagon."""
    return [(center[0] + size * cos(pi / 3 * k - pi / 6),
             center[1] + size * sin(pi / 3 * k - pi / 6)) for k in range(6)]
