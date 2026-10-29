"""Board, disc and legend rendering using only Pygame primitives."""

from math import sqrt, cos, sin, pi
import pygame
from config import COLORS, FONT_BODY, FONT_SMALL, DISC_RADIUS_RATIO, WHITE, BLACK
from hexgrid import CELLS, INDEX, axial_to_pixel, pixel_to_axial, corners
from boardgen import HOLES
from engine import GameState
from ui.widgets import text, tr


def disc(surface: pygame.Surface, center: tuple[float, float], radius: float, owner: int) -> None:
    """Raised circular pieces with a rim distinct from full-footprint holes."""
    x, y, radius = round(center[0]), round(center[1]), round(radius)
    pygame.draw.circle(surface, COLORS["shadow"], (x + 1, y + 3), radius + 2)
    pygame.draw.circle(surface, COLORS["white" if owner == WHITE else "black"], (x, y), radius)
    pygame.draw.circle(surface, COLORS["rim"], (x, y), radius, 2)
    pygame.draw.circle(surface, COLORS["rim" if owner == WHITE else "inner"], (x, y), max(1, radius - 4), 1)


class BoardRenderer:
    """Size is derived from the available board rectangle."""

    def __init__(self, rect: pygame.Rect) -> None:
        self.rect, self.origin = rect, rect.center
        self.size = min(rect.width / 22, rect.height / 19)
        self.centers = tuple(axial_to_pixel(q, r, self.size, self.origin) for q, r in CELLS)

    def hit_test(self, position: tuple[int, int]) -> int | None:
        """Map a pixel to its grid index using cube rounding, including holes."""
        return INDEX.get(pixel_to_axial(*position, self.size, self.origin))

    def draw(self, surface: pygame.Surface, state: GameState, legal: dict[int, tuple[int, ...]],
             show_numbers: bool, focused: int | None = None) -> None:
        """Draw all markers before the centered modifier labels."""
        cx, cy = self.origin
        plate_radius = sqrt(3) * 6 * self.size
        plate = [(cx + plate_radius * cos(pi * k / 3), cy + plate_radius * sin(pi * k / 3)) for k in range(6)]
        for color, width in (("wood", 24), ("plate", 12)):
            pygame.draw.polygon(surface, COLORS[color], plate)
            pygame.draw.lines(surface, COLORS[color], True, plate, width)
            for point in plate:
                pygame.draw.circle(surface, COLORS[color], point, width // 2)
        hover = self.hit_test(pygame.mouse.get_pos())
        for i, center in enumerate(self.centers):
            polygon = corners(center, self.size - 1)
            if i in HOLES:
                pygame.draw.polygon(surface, COLORS["hole"], corners(center, self.size))
                pygame.draw.polygon(surface, COLORS["hole_edge"], corners(center, self.size - 5), 1)
            else:
                modifier = state.board.modifiers[i]
                assert modifier is not None
                pygame.draw.polygon(surface, COLORS["positive" if modifier[0] == "+" else "negative"], polygon)
                pygame.draw.polygon(surface, COLORS["tile_edge"], polygon, 2)
                if i == state.last_move or i == focused or i == hover:
                    pygame.draw.polygon(surface, COLORS["gold" if i == state.last_move or i == focused else "rim"], polygon, 3 if i == focused else 2)
                if state.owners[i]:
                    disc(surface, center, self.size * DISC_RADIUS_RATIO, state.owners[i])
                elif i in legal:
                    pygame.draw.circle(surface, COLORS["white"], (round(center[0]), round(center[1] + self.size * 0.63)), 4, 2)
            if show_numbers:
                text(surface, tr("number", number=i + 1),
                     (center[0], center[1] - self.size * 0.72), 15, center=True)
            if i not in HOLES:
                label = f"{modifier[0]}{modifier[1]}"
                label_color = "black" if state.owners[i] == WHITE else "text"
                if not state.owners[i]:
                    # ASSUMPTION: a one-pixel text shadow keeps light labels legible on tile tints.
                    text(surface, label, (center[0] + 1, center[1] + 1), FONT_BODY, "black", True)
                text(surface, label, center, FONT_BODY, label_color, True)

    def hover_text(self, state: GameState) -> str:
        """Holes have no hover content, highlight or modifier."""
        i = self.hit_test(pygame.mouse.get_pos())
        if i is None or i in HOLES:
            return tr("hover_hint")
        q, r = CELLS[i]
        modifier = state.board.modifiers[i]
        assert modifier is not None
        return tr("hover", number=i + 1, q=q, r=r, modifier=f"{modifier[0]}{modifier[1]}", value=state.board.values[i])

    def legend(self, surface: pygame.Surface, y: int) -> None:
        """Show piece silhouettes, holes and both signed tile tints."""
        labels = ("white_piece", "black_piece", "hole", "empty_cell", "plus", "minus")
        for k, label in enumerate(labels):
            x = 40 + k * 145
            center = (x + 14, y + 15)
            if k < 2:
                disc(surface, center, 12, WHITE if k == 0 else BLACK)
            else:
                color = ("hole", "plate", "positive", "negative")[k - 2]
                pygame.draw.polygon(surface, COLORS[color], corners(center, 16))
                pygame.draw.polygon(surface, COLORS["hole_edge" if k == 2 else "tile_edge"], corners(center, 16), 1)
            text(surface, tr(label), (x + 36, y + 8), FONT_SMALL)
