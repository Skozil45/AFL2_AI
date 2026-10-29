"""Small drawing and focus helpers shared by both screens."""

from dataclasses import dataclass
import pygame
from config import COLORS, STRINGS, FONT_NAME, FONT_BODY, FONT_SMALL


def tr(key: str, **values: object) -> str:
    """Resolve interface text from the translation dictionary."""
    return STRINGS[key].format(**values)


def text(surface: pygame.Surface, value: str, position: tuple[float, float],
         size: int = FONT_BODY, color: str = "text", center: bool = False,
         max_width: int | None = None) -> None:
    """Draw text, shrinking unusually long seeds or translations to fit."""
    font = pygame.font.Font(FONT_NAME, size)
    if max_width:
        while font.size(value)[0] > max_width and size > 12:
            size -= 1
            font = pygame.font.Font(FONT_NAME, size)
    rendered = font.render(value, True, COLORS[color])
    rect = rendered.get_rect()
    if center:
        rect.center = position
    else:
        rect.topleft = position
    surface.blit(rendered, rect)


def wrapped_text(surface: pygame.Surface, value: str, rect: pygame.Rect,
                 color: str = "text", size: int = FONT_SMALL) -> None:
    """Wrap status messages within the panel."""
    font = pygame.font.Font(FONT_NAME, size)
    line, y = "", rect.y
    for word in value.split():
        proposed = f"{line} {word}".strip()
        if line and font.size(proposed)[0] > rect.width:
            text(surface, line, (rect.x, y), size, color)
            y += font.get_linesize()
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
        color = "button" if self.enabled else "disabled"
        pygame.draw.rect(surface, COLORS[color], self.rect, border_radius=6)
        if self.selected or focused or (self.enabled and self.rect.collidepoint(pygame.mouse.get_pos())):
            pygame.draw.rect(surface, COLORS["gold" if focused or self.selected else "rim"],
                             self.rect, 2, border_radius=6)
        text(surface, self.label, self.rect.center, color="text" if self.enabled else "muted",
             center=True, max_width=self.rect.width - 16)


def tab_index(current: int, count: int, backwards: bool = False) -> int:
    """Cycle a linear focus order."""
    return (current + (-1 if backwards else 1)) % count
