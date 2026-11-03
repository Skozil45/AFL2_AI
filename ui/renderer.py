"""Board, disc and legend rendering using only Pygame primitives."""

# =============================================================================
# FILE: ui/renderer.py  -  draws the hex board, and finds the cell under
# the mouse.
#
# The game screen creates one BoardRenderer, giving it the rectangle the
# board must fit in. Then:
#   every frame, GameScreen.draw() calls
#       BoardRenderer.draw()        - the board, tiles and discs
#       BoardRenderer.hover_text()  - the info line at the top
#       BoardRenderer.legend()      - the row of symbols under the board
#   on every click, GameScreen.handle_event() calls
#       BoardRenderer.hit_test()    - which cell was clicked?
#
# This file only READS the game state; it never changes the game.
#
# -----------------------------------------------------------------------------
# CONCEPT: DRAWING ORDER
# -----------------------------------------------------------------------------
# Pygame paints like a painter: whatever is drawn later covers what was
# drawn earlier. So we draw the wooden frame first, then the plate, then
# each tile, its outline, its disc, and finally its label on top.
# =============================================================================

# Maths for the corners of the board plate.
from math import sqrt, cos, sin, pi
# Drawing functions and the mouse position.
import pygame
# Colours, fonts, the disc size, and the player values.
from config import COLORS, FONT_BODY, FONT_SMALL, DISC_RADIUS_RATIO, WHITE, BLACK
# Hex maths (see hexgrid.py).
from hexgrid import CELLS, INDEX, axial_to_pixel, pixel_to_axial, corners
# Holes are drawn differently from tiles.
from boardgen import HOLES
# Only used in type hints; this file never changes the game.
from engine import GameState
# Text drawing and translations.
from ui.widgets import text, tr


# Draws one disc: a shadow, the coloured body, an outer rim and an inner ring.
# Called by BoardRenderer.draw() for every disc, and by legend().
def disc(surface: pygame.Surface, center: tuple[float, float], radius: float, owner: int) -> None:
    """Raised circular pieces with a rim distinct from full-footprint holes."""
    # Pygame needs whole-number pixel positions.
    x, y, radius = round(center[0]), round(center[1]), round(radius)
    # A shadow slightly lower and to the right makes the disc look raised.
    pygame.draw.circle(surface, COLORS["shadow"], (x + 1, y + 3), radius + 2)
    # The disc itself, in white or black.
    pygame.draw.circle(surface, COLORS["white" if owner == WHITE else "black"], (x, y), radius)
    # A light outer rim, 2 pixels wide.
    pygame.draw.circle(surface, COLORS["rim"], (x, y), radius, 2)
    # A thin inner ring, 1 pixel wide, for a 3D look.
    pygame.draw.circle(surface, COLORS["rim" if owner == WHITE else "inner"], (x, y),
                       max(1, radius - 4), 1)


# Created once by GameScreen.__init__, with the area for the board.
class BoardRenderer:
    """Size is derived from the available board rectangle."""

    def __init__(self, rect: pygame.Rect) -> None:
        # The board's area. Cell (0, 0) is drawn at the centre of it.
        self.rect, self.origin = rect, rect.center
        # The hex size in pixels, chosen so the whole board fits the area.
        self.size = min(rect.width / 22, rect.height / 19)
        # The pixel centre of every cell, calculated once.
        self.centers = tuple(axial_to_pixel(q, r, self.size, self.origin) for q, r in CELLS)

    # Returns the index of the cell at a pixel position, or None if the
    # position is outside the board.
    # Called for clicks (handle_event) and for the mouse hover (draw, hover_text).
    def hit_test(self, position: tuple[int, int]) -> int | None:
        """Map a pixel to its grid index using cube rounding, including holes."""
        # Pixel -> nearest (q, r) -> index. INDEX.get returns None if (q, r)
        # is not on the board.
        return INDEX.get(pixel_to_axial(*position, self.size, self.origin))

    # Draws the whole board. Called by GameScreen.draw() every frame.
    #   legal        - the legal moves to mark with a small ring
    #                  (the game screen only passes them on your turn)
    #   show_numbers - True after pressing N
    #   focused      - the cell selected with the Tab key, if any
    def draw(self, surface: pygame.Surface, state: GameState, legal: dict[int, tuple[int, ...]],
             show_numbers: bool, focused: int | None = None) -> None:
        """Draw all markers before the centered modifier labels."""
        # The centre of the board in pixels.
        cx, cy = self.origin
        # The plate reaches a little beyond the outer ring of cells.
        plate_radius = sqrt(3) * 6 * self.size
        # The 6 corners of the plate, one every 60 degrees.
        plate = [(cx + plate_radius * cos(pi * k / 3), cy + plate_radius * sin(pi * k / 3))
                 for k in range(6)]
        # Draw a wide wooden frame first, then a narrower green plate on top.
        for color, width in (("wood", 24), ("plate", 12)):
            # A filled hexagon...
            pygame.draw.polygon(surface, COLORS[color], plate)
            # ...with a thick outline to make it bigger...
            pygame.draw.lines(surface, COLORS[color], True, plate, width)
            # ...and a circle on each corner to round it off.
            for point in plate:
                pygame.draw.circle(surface, COLORS[color], point, width // 2)
        # The cell under the mouse, to give it a hover outline.
        hover = self.hit_test(pygame.mouse.get_pos())
        # Now draw every cell. "i" is its index, "center" its pixel centre.
        for i, center in enumerate(self.centers):
            # The tile's hexagon, 1 pixel smaller to leave a thin gap.
            polygon = corners(center, self.size - 1)
            # A hole: a dark full-size hexagon with a faint inner outline.
            if i in HOLES:
                pygame.draw.polygon(surface, COLORS["hole"], corners(center, self.size))
                pygame.draw.polygon(surface, COLORS["hole_edge"], corners(center, self.size - 5), 1)
            # A playable tile:
            else:
                # Its modifier, for example ("+", 3).
                modifier = state.board.modifiers[i]
                # "assert" stops the program if this is ever not true.
                # Only holes have no modifier, and this is not a hole.
                assert modifier is not None
                # Fill: green for a "+" tile, brown for a "-" tile.
                pygame.draw.polygon(surface, COLORS["positive" if modifier[0] == "+" else "negative"],
                                    polygon)
                # The tile's outline.
                pygame.draw.polygon(surface, COLORS["tile_edge"], polygon, 2)
                # Highlight the last move or the focused cell in gold, and the
                # cell under the mouse in grey.
                if i == state.last_move or i == focused or i == hover:
                    pygame.draw.polygon(surface,
                                        COLORS["gold" if i == state.last_move or i == focused
                                               else "rim"],
                                        polygon, 3 if i == focused else 2)
                # If someone owns this tile, draw their disc.
                # (EMPTY is 0, and 0 counts as False in an "if".)
                if state.owners[i]:
                    disc(surface, center, self.size * DISC_RADIUS_RATIO, state.owners[i])
                # If it is empty and a legal move, draw a small ring near the bottom.
                elif i in legal:
                    pygame.draw.circle(surface, COLORS["white"],
                                       (round(center[0]), round(center[1] + self.size * 0.63)),
                                       4, 2)
            # After pressing N: the cell number near the top of the cell.
            if show_numbers:
                text(surface, tr("number", number=i + 1),
                     (center[0], center[1] - self.size * 0.72), 15, center=True)
            # Every playable tile shows its modifier, for example "+3".
            if i not in HOLES:
                label = f"{modifier[0]}{modifier[1]}"
                # Dark text on a White disc, white text everywhere else.
                label_color = "black" if state.owners[i] == WHITE else "text"
                # On an empty tile, first draw a dark copy 1 pixel lower-right
                # as a shadow, so the text is easier to read.
                if not state.owners[i]:
                    # ASSUMPTION: a one-pixel text shadow keeps light labels legible on tile tints.
                    text(surface, label, (center[0] + 1, center[1] + 1), FONT_BODY, "black", True)
                # The label itself, centred on the tile.
                text(surface, label, center, FONT_BODY, label_color, True)

    # Returns the info line about the tile under the mouse.
    # Called by GameScreen.draw() every frame.
    def hover_text(self, state: GameState) -> str:
        """Holes have no hover content, highlight or modifier."""
        # The cell under the mouse.
        i = self.hit_test(pygame.mouse.get_pos())
        # Outside the board or over a hole: show the general hint instead.
        if i is None or i in HOLES:
            return tr("hover_hint")
        # The tile's coordinates and modifier.
        q, r = CELLS[i]
        modifier = state.board.modifiers[i]
        assert modifier is not None
        # For example: "#12  (1, -4)   +3   value +4".
        return tr("hover", number=i + 1, q=q, r=r, modifier=f"{modifier[0]}{modifier[1]}",
                  value=state.board.values[i])

    # Draws the row of symbols under the board, at height y.
    # Called by GameScreen.draw() every frame.
    def legend(self, surface: pygame.Surface, y: int) -> None:
        """Show piece silhouettes, holes and both signed tile tints."""
        # The STRINGS keys of the six entries, from left to right.
        labels = ("white_piece", "black_piece", "hole", "empty_cell", "plus", "minus")
        # Draw one entry at a time. k is 0 to 5.
        for k, label in enumerate(labels):
            # Each entry is 145 pixels to the right of the previous one.
            x = 40 + k * 145
            # The centre of the small symbol.
            center = (x + 14, y + 15)
            # The first two entries are discs: White, then Black.
            if k < 2:
                disc(surface, center, 12, WHITE if k == 0 else BLACK)
            # The others are small hexagons: hole, empty plate, "+" tile, "-" tile.
            else:
                color = ("hole", "plate", "positive", "negative")[k - 2]
                pygame.draw.polygon(surface, COLORS[color], corners(center, 16))
                pygame.draw.polygon(surface, COLORS["hole_edge" if k == 2 else "tile_edge"],
                                    corners(center, 16), 1)
            # The label to the right of the symbol.
            text(surface, tr(label), (x + 36, y + 8), FONT_SMALL)
