"""Desktop entry point: python main.py."""

import pygame
import config
from engine import assert_opening
from ui.setup_screen import SetupScreen
from ui.game_screen import GameScreen


def main() -> None:
    """Run the 60 FPS event loop; all engine logic remains headless-testable."""
    assert_opening()
    pygame.init()
    surface = pygame.display.set_mode(config.WINDOW_SIZE)
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
