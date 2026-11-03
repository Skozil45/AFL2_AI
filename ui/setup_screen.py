"""Pre-match algorithm, depth and integer seed controls."""

# =============================================================================
# FILE: ui/setup_screen.py  -  the first screen of the app.
#
# How it is used:
#   1. main.py creates SetupScreen() at the start (and after "New Setup").
#   2. Every frame, main.py calls handle_event() for each event, then draw().
#   3. You choose Greedy or Minimax, a depth (Minimax only) and a seed.
#   4. Pressing "Start game" (or Enter in the seed box) calls start().
#      If the seed is valid, start() returns a Settings object.
#   5. handle_event() passes it back to main.py, which opens
#      GameScreen(settings).
#
# -----------------------------------------------------------------------------
# CONCEPT: KEYBOARD FOCUS
# -----------------------------------------------------------------------------
# targets() lists every control in Tab order. self.focus is the position in
# that list of the control the keyboard is on (it gets a gold border).
# Tab moves forward, Shift+Tab moves back, and Enter or Space activates it.
# =============================================================================

# dataclass writes the __init__ method of Settings for us.
from dataclasses import dataclass
# Unpredictable random numbers, used for a blank seed.
import secrets
# Rectangles, events and drawing.
import pygame
# Colours, texts, the time limit and the seed size.
import config
# Shared helpers: buttons, text, translations, Tab focus.
from ui.widgets import Button, text, tr, tab_index


# The choices for one match.
# Created by SetupScreen.start() and read by GameScreen.
@dataclass(frozen=True)
class Settings:
    """Validated choices for a match."""

    # "greedy" or "minimax".
    algorithm: str
    # The Minimax depth, 1 to 4 (Greedy ignores it).
    depth: int
    # The seed for the board's random modifiers.
    seed: int


class SetupScreen:
    """Single setup form with mouse and Tab/Enter support."""

    # Creates the screen with its buttons and default choices.
    # Called by main.py.
    def __init__(self) -> None:
        # ASSUMPTION: setup defaults to Greedy; remembered Minimax depth starts at 2.
        self.algorithm, self.depth, self.seed_text = "greedy", 2, ""
        # The error under the seed box ("" means no error).
        self.error = ""
        # Which control has keyboard focus (a position in targets()).
        self.focus = 0
        # The seed text box: x, y, width, height.
        self.seed_rect = pygame.Rect(400, 399, 480, 48)
        # Two buttons side by side: Greedy, then Minimax.
        self.algorithm_buttons = [Button(pygame.Rect(400 + i * 245, 211, 235, 48), tr(key))
                                  for i, key in enumerate(("greedy", "minimax"))]
        # Four small buttons in a row, labelled 1 to 4.
        self.depth_buttons = [Button(pygame.Rect(400 + i * 80, 305, 68, 44),
                                     tr("depth_number", depth=i + 1)) for i in range(4)]
        # The big "Start game" button.
        self.start_button = Button(pygame.Rect(400, 620, 480, 52), tr("start"))

    # Returns every control in Tab order. The depth buttons are only
    # included when Minimax is chosen.
    # Called by handle_event() and draw().
    def targets(self) -> list[Button | pygame.Rect]:
        """Disabled depth buttons are omitted from keyboard navigation."""
        return (self.algorithm_buttons
                + (self.depth_buttons if self.algorithm == "minimax" else [])
                + [self.seed_rect, self.start_button])

    # Checks the seed and returns the Settings, or None if the seed is invalid.
    # Called when "Start game" is activated or Enter is pressed in the seed box.
    def start(self) -> Settings | None:
        """Validate the input before choosing a random seed if blank."""
        # int() raises ValueError for text that is not a whole number.
        try:
            # Use the typed number, or a random 32-bit number if the box is blank.
            seed = (int(self.seed_text.strip()) if self.seed_text.strip()
                    else secrets.randbits(config.SEED_BITS))
        except ValueError:
            # Not a whole number: show the error and stay on this screen.
            self.error = tr("seed_error")
            return None
        # Valid: main.py will now open the game screen.
        return Settings(self.algorithm, self.depth, seed)

    # Performs a control's action. Called by handle_event() for a click,
    # or for Enter or Space on the focused control.
    def activate(self, target: Button | pygame.Rect) -> Settings | None:
        """Apply a selection or submit the form."""
        # "Start game": check the seed and maybe return Settings.
        if target is self.start_button:
            return self.start()
        # Was it one of the algorithm buttons?
        for i, button in enumerate(self.algorithm_buttons):
            if target is button:
                # Choose that algorithm.
                self.algorithm = ("greedy", "minimax")[i]
                # Keep the focus on this button. (The targets() list just
                # changed length, so the old focus position may be wrong.)
                self.focus = i
        # Was it one of the depth buttons?
        for i, button in enumerate(self.depth_buttons):
            if target is button:
                self.depth = i + 1  # Choose depth 1 to 4.
        # Nothing to start yet.
        return None

    # Reacts to one event. Called by main.py for every event.
    # Returns Settings only when a valid start happened, otherwise None.
    def handle_event(self, event: pygame.event.Event) -> Settings | None:
        """Consume setup events; return settings only for a valid start."""
        # The controls that exist right now, in Tab order.
        targets = self.targets()
        # A left mouse click...
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # ...check every control...
            for i, target in enumerate(targets):
                # (the seed box is a plain Rect, the others are Buttons)
                rect = target.rect if isinstance(target, Button) else target
                # ...to see if the click was inside it.
                if rect.collidepoint(event.pos):
                    self.focus = i  # The keyboard focus follows the click.
                    return self.activate(target)  # Perform its action.
        # A key press...
        if event.type == pygame.KEYDOWN:
            # Tab or Shift+Tab moves the focus forward or back.
            if event.key == pygame.K_TAB:
                self.focus = tab_index(self.focus, len(targets), bool(event.mod & pygame.KMOD_SHIFT))
            # Enter in the seed box starts the game; elsewhere it activates.
            elif event.key == pygame.K_RETURN:
                return (self.start() if targets[self.focus] is self.seed_rect
                        else self.activate(targets[self.focus]))
            # Space activates a button (in the seed box it is typed instead).
            elif event.key == pygame.K_SPACE and targets[self.focus] is not self.seed_rect:
                return self.activate(targets[self.focus])
            # Any other key while the seed box has focus edits the seed:
            elif targets[self.focus] is self.seed_rect:
                # Backspace deletes the last character.
                if event.key == pygame.K_BACKSPACE:
                    self.seed_text = self.seed_text[:-1]
                # Ctrl+A clears the whole box.
                elif event.key == pygame.K_a and event.mod & pygame.KMOD_CTRL:
                    self.seed_text = ""
                # A normal character is added (start() checks it later).
                elif event.unicode and event.unicode.isprintable():
                    self.seed_text += event.unicode
                # Any edit hides the old error.
                self.error = ""
        # No match to start.
        return None

    # Draws the setup screen. Called by main.py every frame.
    def draw(self, surface: pygame.Surface) -> None:
        """Render the setup form and fixed rules."""
        # Clear the whole window.
        surface.fill(config.COLORS["background"])
        # Title and subtitle, centred at x = 640 (the middle of the window).
        text(surface, tr("title"), (640, 79), config.FONT_TITLE, center=True)
        text(surface, tr("subtitle"), (640, 126), color="muted", center=True)
        # Labels for the three settings, and the hint under the depth buttons.
        text(surface, tr("algorithm"), (400, 181))
        text(surface, tr("depth"), (400, 277))
        text(surface, tr("depth_note"), (400, 356), config.FONT_SMALL, "muted")
        text(surface, tr("seed_label"), (400, 374))
        # Needed to know which control has focus.
        targets = self.targets()
        # Mark the chosen algorithm as selected.
        for i, button in enumerate(self.algorithm_buttons):
            button.selected = self.algorithm == ("greedy", "minimax")[i]
        # The depth buttons are usable only with Minimax, and the chosen
        # depth is marked as selected.
        for i, button in enumerate(self.depth_buttons):
            button.enabled, button.selected = (self.algorithm == "minimax",
                                               self.depth == i + 1 and self.algorithm == "minimax")
        # Draw every button, with a focus border on the focused one.
        for button in self.algorithm_buttons + self.depth_buttons + [self.start_button]:
            button.draw(surface, targets[self.focus] is button)
        # The seed box: background, then a border (gold when it has focus).
        pygame.draw.rect(surface, config.COLORS["panel"], self.seed_rect, border_radius=4)
        pygame.draw.rect(surface,
                         config.COLORS["gold" if targets[self.focus] is self.seed_rect else "rim"],
                         self.seed_rect, 2, border_radius=4)
        # The seed you typed.
        text(surface, self.seed_text, (413, 413), max_width=self.seed_rect.width - 26)
        # The error message (an empty string draws nothing visible).
        text(surface, self.error, (400, 458), config.FONT_SMALL, "red")
        # Three lines of fixed rule information, 31 pixels apart: holes,
        # modifier range, and the time limit (or "disabled" if there is none).
        for i, label in enumerate((tr("holes_info"), tr("range_info"),
                                   tr("limit_info", limit=config.TURN_TIME_LIMIT_SECONDS)
                                   if config.TURN_TIME_LIMIT_SECONDS is not None
                                   else tr("limit_off"))):
            text(surface, label, (400, 500 + i * 31), color="muted")
        # Keyboard help at the bottom.
        text(surface, tr("keys"), (640, 715), config.FONT_SMALL, "muted", center=True)
