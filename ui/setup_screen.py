"""Pre-match algorithm, depth and integer seed controls."""

from dataclasses import dataclass
import secrets
import pygame
import config
from ui.widgets import Button, text, tr, tab_index


@dataclass(frozen=True)
class Settings:
    """Validated choices for a match."""

    algorithm: str
    depth: int
    seed: int


class SetupScreen:
    """Single setup form with mouse and Tab/Enter support."""

    def __init__(self) -> None:
        # ASSUMPTION: setup defaults to Greedy; remembered Minimax depth starts at 2.
        self.algorithm, self.depth, self.seed_text = "greedy", 2, ""
        self.error = ""
        self.focus = 0
        self.seed_rect = pygame.Rect(400, 399, 480, 48)
        self.algorithm_buttons = [Button(pygame.Rect(400 + i * 245, 211, 235, 48), tr(key))
                                  for i, key in enumerate(("greedy", "minimax"))]
        self.depth_buttons = [Button(pygame.Rect(400 + i * 80, 305, 68, 44),
                                     tr("depth_number", depth=i + 1)) for i in range(4)]
        self.start_button = Button(pygame.Rect(400, 620, 480, 52), tr("start"))

    def targets(self) -> list[Button | pygame.Rect]:
        """Disabled depth buttons are omitted from keyboard navigation."""
        return self.algorithm_buttons + (self.depth_buttons if self.algorithm == "minimax" else []) + [self.seed_rect, self.start_button]

    def start(self) -> Settings | None:
        """Validate the input before choosing a random seed if blank."""
        try:
            seed = int(self.seed_text.strip()) if self.seed_text.strip() else secrets.randbits(config.SEED_BITS)
        except ValueError:
            self.error = tr("seed_error")
            return None
        return Settings(self.algorithm, self.depth, seed)

    def activate(self, target: Button | pygame.Rect) -> Settings | None:
        """Apply a selection or submit the form."""
        if target is self.start_button:
            return self.start()
        for i, button in enumerate(self.algorithm_buttons):
            if target is button:
                self.algorithm = ("greedy", "minimax")[i]
                self.focus = i
        for i, button in enumerate(self.depth_buttons):
            if target is button:
                self.depth = i + 1
        return None

    def handle_event(self, event: pygame.event.Event) -> Settings | None:
        """Consume setup events; return settings only for a valid start."""
        targets = self.targets()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, target in enumerate(targets):
                rect = target.rect if isinstance(target, Button) else target
                if rect.collidepoint(event.pos):
                    self.focus = i
                    return self.activate(target)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self.focus = tab_index(self.focus, len(targets), bool(event.mod & pygame.KMOD_SHIFT))
            elif event.key == pygame.K_RETURN:
                return self.start() if targets[self.focus] is self.seed_rect else self.activate(targets[self.focus])
            elif event.key == pygame.K_SPACE and targets[self.focus] is not self.seed_rect:
                return self.activate(targets[self.focus])
            elif targets[self.focus] is self.seed_rect:
                if event.key == pygame.K_BACKSPACE:
                    self.seed_text = self.seed_text[:-1]
                elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                    self.seed_text = ""
                elif event.unicode and event.unicode.isprintable():
                    self.seed_text += event.unicode
                self.error = ""
        return None

    def draw(self, surface: pygame.Surface) -> None:
        """Render the setup form and fixed rules."""
        surface.fill(config.COLORS["background"])
        text(surface, tr("title"), (640, 79), config.FONT_TITLE, center=True)
        text(surface, tr("subtitle"), (640, 126), color="muted", center=True)
        text(surface, tr("algorithm"), (400, 181))
        text(surface, tr("depth"), (400, 277))
        text(surface, tr("depth_note"), (400, 356), config.FONT_SMALL, "muted")
        text(surface, tr("seed_label"), (400, 374))
        targets = self.targets()
        for i, button in enumerate(self.algorithm_buttons):
            button.selected = self.algorithm == ("greedy", "minimax")[i]
        for i, button in enumerate(self.depth_buttons):
            button.enabled, button.selected = self.algorithm == "minimax", self.depth == i + 1 and self.algorithm == "minimax"
        for button in self.algorithm_buttons + self.depth_buttons + [self.start_button]:
            button.draw(surface, targets[self.focus] is button)
        pygame.draw.rect(surface, config.COLORS["panel"], self.seed_rect, border_radius=4)
        pygame.draw.rect(surface, config.COLORS["gold" if targets[self.focus] is self.seed_rect else "rim"], self.seed_rect, 2, border_radius=4)
        text(surface, self.seed_text, (413, 413), max_width=self.seed_rect.width - 26)
        text(surface, self.error, (400, 458), config.FONT_SMALL, "red")
        for i, label in enumerate((tr("holes_info"), tr("range_info"),
                                   tr("limit_info", limit=config.TURN_TIME_LIMIT_SECONDS) if config.TURN_TIME_LIMIT_SECONDS is not None else tr("limit_off"))):
            text(surface, label, (400, 500 + i * 31), color="muted")
        text(surface, tr("keys"), (640, 715), config.FONT_SMALL, "muted", center=True)
