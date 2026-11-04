"""Scaled, anti-aliased drawing: screens use WINDOW_SIZE coordinates, this maps them to real pixels."""

from functools import lru_cache
from math import hypot
import pygame
from config import WINDOW_SIZE

Point = tuple[float, float]
Color = str | tuple[int, int, int, int]
_scale = 1.0


def set_scale(scale: float) -> None:
    """Choose how many real pixels one layout unit covers."""
    global _scale
    _scale = scale


def px(value: float) -> int:
    """Convert a layout length to whole real pixels."""
    return round(value * _scale)


def window_size() -> tuple[int, int]:
    """The window's size in real pixels."""
    return px(WINDOW_SIZE[0]), px(WINDOW_SIZE[1])


def to_screen(point: Point) -> Point:
    """Convert a layout position to a real-pixel position."""
    return point[0] * _scale, point[1] * _scale


def to_layout(point: tuple[int, int]) -> tuple[int, int]:
    """Convert a real-pixel position, such as a click, to layout coordinates."""
    return round(point[0] / _scale), round(point[1] / _scale)


def mouse_pos() -> tuple[int, int]:
    """The mouse position in layout coordinates."""
    return to_layout(pygame.mouse.get_pos())


def polygon(surface: pygame.Surface, color: Color, points: list[Point]) -> None:
    """Filled polygon with smooth edges."""
    scaled = [to_screen(point) for point in points]
    pygame.draw.polygon(surface, color, scaled)
    pygame.draw.aalines(surface, color, True, scaled)


def circle(surface: pygame.Surface, color: Color, center: Point, radius: float, width: float = 0) -> None:
    """Smooth circle, filled unless a ring width is given."""
    pygame.draw.aacircle(surface, color, to_screen(center), radius * _scale, max(1, px(width)) if width else 0)


def stroke(surface: pygame.Surface, color: Color, points: list[Point], width: float) -> None:
    """Thick closed outline with rounded corners."""
    half = width / 2
    for (ax, ay), (bx, by) in zip(points, points[1:] + points[:1]):
        length = hypot(bx - ax, by - ay)
        nx, ny = (ay - by) / length * half, (bx - ax) / length * half
        polygon(surface, color, [(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
    for point in points:
        circle(surface, color, point, half)


@lru_cache(maxsize=None)
def _rounded(size: tuple[int, int], color: Color, width: int, radius: int) -> pygame.Surface:
    """Rounded rectangle drawn four times larger, then shrunk to smooth its corners."""
    large = pygame.Surface((size[0] * 4, size[1] * 4), pygame.SRCALPHA)
    large.fill((*pygame.Color(color)[:3], 0))
    pygame.draw.rect(large, color, large.get_rect(), width * 4, border_radius=radius * 4)
    return pygame.transform.smoothscale(large, size)


def rect(surface: pygame.Surface, color: Color, area: pygame.Rect | tuple[float, float, float, float],
         width: float = 0, border_radius: float = 0) -> None:
    """Rectangle whose edges land on whole pixels, with smooth rounded corners."""
    x, y, w, h = area
    left, top = px(x), px(y)
    target = pygame.Rect(left, top, px(x + w) - left, px(y + h) - top)
    line = max(1, px(width)) if width else 0
    if border_radius:
        surface.blit(_rounded(target.size, color, line, px(border_radius)), target)
    else:
        pygame.draw.rect(surface, color, target, line)
