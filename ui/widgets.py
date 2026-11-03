"""Small drawing and focus helpers shared by both screens."""

# =============================================================================
# FILE: ui/widgets.py  -  small building blocks used by every screen.
#
#   tr()           - get a text from config.STRINGS and fill in its values
#   text()         - draw one line of text
#   wrapped_text() - draw a message over several lines
#   Button         - a rectangle you can click or select with the keyboard
#   tab_index()    - move the keyboard focus with Tab
#
# The screens call these from their draw() and handle_event() methods,
# so they run every frame.
#
# -----------------------------------------------------------------------------
# CONCEPT: HOW PYGAME DRAWS TEXT
# -----------------------------------------------------------------------------
# Pygame cannot write text straight onto the window. Instead:
#   1. load a Font at a size,
#   2. font.render() turns the text into a small image,
#   3. surface.blit() copies that image onto the window at a position.
# =============================================================================

# dataclass writes the __init__ method of Button for us.
from dataclasses import dataclass
# Fonts, drawing and the mouse position.
import pygame
# Colours, texts and font settings.
from config import COLORS, STRINGS, FONT_NAME, FONT_BODY, FONT_SMALL


# Returns a text from config.STRINGS with its {placeholders} filled in.
# Example: tr("score", name="AI", score=5) returns "AI: 5 points".
# "**values" collects any named arguments (name="AI", score=5) into a
# dictionary, and .format(**values) puts them into the {braces}.
def tr(key: str, **values: object) -> str:
    """Resolve interface text from the translation dictionary."""
    return STRINGS[key].format(**values)


# Draws one line of text.
# position is the top-left corner, or the centre if center=True.
# If max_width is given, the font gets smaller until the text fits.
# Called many times per frame by every draw() method.
def text(surface: pygame.Surface, value: str, position: tuple[float, float],
         size: int = FONT_BODY, color: str = "text", center: bool = False,
         max_width: int | None = None) -> None:
    """Draw text, shrinking unusually long seeds or translations to fit."""
    # Step 1: load the font at the requested size.
    font = pygame.font.Font(FONT_NAME, size)
    # If there is a width limit...
    if max_width:
        # ...and the text is too wide (but never go below 12 pixels)...
        while font.size(value)[0] > max_width and size > 12:
            size -= 1  # ...try a font one pixel smaller...
            font = pygame.font.Font(FONT_NAME, size)  # ...and load it.
    # Step 2: turn the text into an image. True = smooth edges.
    rendered = font.render(value, True, COLORS[color])
    # The image's rectangle, which we can move into position.
    rect = rendered.get_rect()
    if center:
        rect.center = position  # Put the middle of the text at position.
    else:
        rect.topleft = position  # Put the top-left corner at position.
    # Step 3: copy the text image onto the window.
    surface.blit(rendered, rect)


# Draws a message inside a rectangle, starting a new line whenever the next
# word would not fit. Called by the game screen for messages and errors.
def wrapped_text(surface: pygame.Surface, value: str, rect: pygame.Rect,
                 color: str = "text", size: int = FONT_SMALL) -> None:
    """Wrap status messages within the panel."""
    # Used to measure how wide the words are.
    font = pygame.font.Font(FONT_NAME, size)
    # The line we are building, and the height where it will be drawn.
    line, y = "", rect.y
    # Go through the message one word at a time.
    for word in value.split():
        # What the line would be with this word added.
        proposed = f"{line} {word}".strip()
        # If that is too wide (and the line already has words)...
        if line and font.size(proposed)[0] > rect.width:
            text(surface, line, (rect.x, y), size, color)  # ...draw the line so far,
            y += font.get_linesize()  # move down one line,
            line = word  # and start the next line with this word.
        else:
            line = proposed  # It fits: keep the word on this line.
    # Draw the last line (shrunk if a single word is too long).
    text(surface, line, (rect.x, y), size, color, max_width=rect.width)


# A button. The screens create their buttons in __init__, check clicks with
# button.rect.collidepoint(), and call button.draw() every frame.
# The button itself does not know what it does; the screen decides that.
@dataclass
class Button:
    """A mouse and keyboard target; owning screens route activation."""

    # Position and size on screen.
    rect: pygame.Rect
    # The text on the button.
    label: str
    # A disabled button is grey (for example the depth buttons with Greedy).
    enabled: bool = True
    # A selected button has a gold border (for example the chosen algorithm).
    selected: bool = False

    # Draws the button. Called by the screen's draw() every frame.
    # focused = True when the button was chosen with the Tab key.
    def draw(self, surface: pygame.Surface, focused: bool = False) -> None:
        """Show enabled, selected, hover, and keyboard focus states."""
        # Normal colour if usable, grey if disabled.
        color = "button" if self.enabled else "disabled"
        # The button's background, with rounded corners.
        pygame.draw.rect(surface, COLORS[color], self.rect, border_radius=6)
        # Draw a border if the button is selected, focused, or enabled and
        # under the mouse: gold for selected or focused, light grey for the mouse.
        if self.selected or focused or (self.enabled
                                        and self.rect.collidepoint(pygame.mouse.get_pos())):
            pygame.draw.rect(surface, COLORS["gold" if focused or self.selected else "rim"],
                             self.rect, 2, border_radius=6)
        # The label in the middle, dimmed if disabled, shrunk if too long.
        text(surface, self.label, self.rect.center, color="text" if self.enabled else "muted",
             center=True, max_width=self.rect.width - 16)


# Returns the next focus position (or the previous one with Shift+Tab).
# "% count" makes it wrap around: after the last item comes the first.
# Called by both screens when Tab is pressed.
def tab_index(current: int, count: int, backwards: bool = False) -> int:
    """Cycle a linear focus order."""
    return (current + (-1 if backwards else 1)) % count
