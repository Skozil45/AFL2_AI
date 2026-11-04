"""Desktop entry point: python main.py."""

import ctypes
import pygame
import config
from engine import assert_opening
from ui import gfx
from ui.setup_screen import SetupScreen
from ui.game_screen import GameScreen


def use_real_pixels() -> float:
    """Stop Windows stretching the window; return the screen's scaling (1.5 means 150%)."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
        return ctypes.windll.user32.GetDpiForSystem() / 96
    except (AttributeError, OSError):
        return 1.0


def fit_to_screen(scale: float) -> float:
    """Shrink the scale if the window would not fit on the screen."""
    width, height = pygame.display.get_desktop_sizes()[0]
    return min(scale, width / config.WINDOW_SIZE[0], (height - config.SCREEN_MARGIN) / config.WINDOW_SIZE[1])


def main() -> None:
    """Run the 60 FPS event loop; all engine logic remains headless-testable."""
    assert_opening()
    screen_scale = use_real_pixels()
    pygame.init()
    gfx.set_scale(fit_to_screen(screen_scale))
    surface = pygame.display.set_mode(gfx.window_size())
    pygame.display.set_caption(config.STRINGS["title"])
    clock = pygame.time.Clock()
    screen: SetupScreen | GameScreen = SetupScreen()
    running = True
    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break
                if event.type == pygame.MOUSEBUTTONDOWN:
                    event = pygame.event.Event(event.type, {**event.dict, "pos": gfx.to_layout(event.pos)})
                result = screen.handle_event(event)
                if isinstance(screen, SetupScreen) and result is not None:
                    screen = GameScreen(result)
                elif result == "setup":
                    screen = SetupScreen()
            if isinstance(screen, GameScreen):
                screen.update()
            screen.draw(surface)
            pygame.display.flip()
            clock.tick(config.FPS)
    finally:
        if isinstance(screen, GameScreen):
            screen.close()
        pygame.quit()


if __name__ == "__main__":
    main()
