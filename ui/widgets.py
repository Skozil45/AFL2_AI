"""Small drawing and focus helpers shared by both screens."""

from dataclasses import dataclass
from functools import lru_cache
import pygame
from config import COLORS, STRINGS, FONT_NAME, FONT_BODY, FONT_SMALL
from ui import gfx


@lru_cache(maxsize=None)
def load_font(size: int) -> pygame.font.Font:
    """Load each font size once; opening a font every frame is slow."""
    return pygame.font.Font(FONT_NAME, size)


def tr(key: str, **values: object) -> str:
    """Resolve interface text from the translation dictionary."""
    return STRINGS[key].format(**values)


def text(surface: pygame.Surface, value: str, position: tuple[float, float],
         size: int = FONT_BODY, color: str = "text", center: bool = False,
         max_width: int | None = None) -> None:
    """Draw text, shrinking unusually long seeds or translations to fit."""
    pixels = gfx.px(size)
    if max_width:
        while load_font(pixels).size(value)[0] > gfx.px(max_width) and pixels > gfx.px(12):
            pixels -= 1
    rendered = load_font(pixels).render(value, True, COLORS[color])
    rect = rendered.get_rect()
    x, y = gfx.to_screen(position)
    if center:
        rect.center = round(x), round(y)
    else:
        rect.topleft = round(x), round(y)
    surface.blit(rendered, rect)


def wrapped_text(surface: pygame.Surface, value: str, rect: pygame.Rect,
                 color: str = "text", size: int = FONT_SMALL) -> None:
    """Wrap status messages within the panel."""
    font = load_font(gfx.px(size))
    line, y = "", rect.y
    for word in value.split():
        proposed = f"{line} {word}".strip()
        if line and font.size(proposed)[0] > gfx.px(rect.width):
            text(surface, line, (rect.x, y), size, color)
            y += font.get_linesize() / gfx.px(size) * size
            line = word
        else:
            line = proposed
    text(surface, line, (rect.x, y), size, color, max_width=rect.width)


@dataclass
class Button:
    """A mouse and keyboard target; owning screens route activation."""

    rect: pygame.Rect
    label: str
    enabled: bool = True
    selected: bool = False

    def draw(self, surface: pygame.Surface, focused: bool = False) -> None:
        """Show enabled, selected, hover, and keyboard focus states."""
        color = "gold" if self.selected else "button" if self.enabled else "disabled"
        gfx.rect(surface, COLORS[color], self.rect, border_radius=6)
        if self.enabled and not self.selected and self.rect.collidepoint(gfx.mouse_pos()):
            gfx.rect(surface, COLORS["rim"], self.rect, 2, border_radius=6)
        if focused:
            gfx.rect(surface, COLORS["gold"], self.rect.inflate(10, 10), 2, border_radius=9)
        label_color = "black" if self.selected else "text" if self.enabled else "muted"
        text(surface, self.label, self.rect.center, color=label_color, center=True, max_width=self.rect.width - 16)


def tab_index(current: int, count: int, backwards: bool = False) -> int:
    """Cycle a linear focus order."""
    return (current + (-1 if backwards else 1)) % count
