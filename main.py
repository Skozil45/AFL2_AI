"""Desktop entry point: python main.py."""

# =============================================================================
# FILE: main.py  -  the starting point of the whole application.
# Run it with:   python main.py
#
# -----------------------------------------------------------------------------
# READING GUIDE  (if you are new to this project, read the files in this order)
# -----------------------------------------------------------------------------
#   1. main.py              <- you are here: how the app starts and loops
#   2. config.py            all fixed numbers, colours and texts
#   3. hexgrid.py           hexagon coordinates (with a small drawing)
#   4. modifiers.py         how a tile like "+3" becomes 4 points
#   5. boardgen.py          building the board from a seed
#   6. engine.py            the game rules (with a capture example)
#   7. ai.py                Greedy and Minimax (with a Minimax example)
#   8. ui/widgets.py        text and buttons
#   9. ui/setup_screen.py   the first screen
#  10. ui/renderer.py       drawing the board
#  11. ui/game_screen.py    running a match (with a threads explanation)
#
# -----------------------------------------------------------------------------
# OVERALL FLOW OF THE APP  (follow the numbers)
# -----------------------------------------------------------------------------
#  1. main() runs engine.assert_opening(): a quick self-check that the board
#     data in config.py is correct (91 cells, 72 playable, 19 holes, and the
#     6 expected first moves).
#  2. Pygame opens a window and the first screen is SetupScreen, where you
#     choose Greedy or Minimax, a search depth (1-4) and a seed.
#  3. The MAIN LOOP repeats 60 times per second. Each repetition is a "frame":
#       a) every input event (mouse click, key press) goes to the current
#          screen's handle_event();
#       b) on the game screen, update() moves the game forward
#          (turn timer, AI answer, passes, game over);
#       c) draw() paints the whole picture, and display.flip() shows it.
#  4. When you press "Start game", SetupScreen.handle_event() returns a
#     Settings object, and main() switches to GameScreen(settings).
#  5. Inside GameScreen:
#       - Your turn: clicking a legal tile plays it (engine.apply_move).
#         If your 30 seconds run out, your turn is skipped.
#       - AI turn: the AI thinks in the background (ai.py) so the window
#         does not freeze, then its move is played.
#  6. At game over you can choose "Play Again" (same board) or "New Setup"
#     (handle_event returns "setup" and main() goes back to SetupScreen).
#  7. Closing the window ends the loop; the "finally" block stops any AI
#     that is still thinking and shuts Pygame down.
#
# -----------------------------------------------------------------------------
# PYTHON FEATURES USED IN THIS PROJECT  (a small glossary)
# -----------------------------------------------------------------------------
#  import x / from x import y
#      Load code from another file. "from engine import GameState" lets us
#      write GameState instead of engine.GameState.
#
#  def name(a: int, b: str = "x") -> bool:
#      Defines a function. ": int" and "-> bool" are TYPE HINTS: they only
#      document what type is expected or returned; Python does not enforce
#      them. "= 'x'" is a default value used when the caller leaves it out.
#
#  int | None
#      A type hint meaning "an int, or None (no value)".
#
#  tuple[int, ...]
#      A type hint meaning "a tuple of any number of ints".
#
#  class Name:  /  self
#      A class is a blueprint for objects. Inside its methods, "self" is the
#      object the method was called on, e.g. self.turn is "this game's turn".
#
#  __init__
#      The method that runs automatically when an object is created, for
#      example GameScreen(settings) runs GameScreen.__init__(settings).
#
#  @dataclass
#      A decorator that writes __init__ for you from the listed fields.
#      @dataclass(frozen=True) also makes the object read-only.
#
#  [x * 2 for x in items]    (list comprehension)
#      A short way to build a list: "x * 2 for every x in items".
#      The same idea works for dicts {k: v for ...} and tuples tuple(...).
#
#  f"Hello {name}"           (f-string)
#      A string with a value inserted in the {braces}.
#
#  a if condition else b
#      Picks a when the condition is true, otherwise b.
#
#  a, b = 1, 2
#      Assigns several variables at once (a = 1 and b = 2).
#
#  try: ... except Error: ... finally: ...
#      try runs code that may fail; except handles a specific error;
#      else runs only if nothing failed; finally ALWAYS runs at the end.
#
#  raise ValueError("...")
#      Stops the current function with an error message.
#
#  isinstance(x, SomeClass)
#      True if x is an object of that class.
#
#  if __name__ == "__main__":
#      True only when this file is run directly (python main.py), not
#      when it is imported. See the bottom of this file.
# =============================================================================

# Pygame is the game library: window, drawing, events, fonts and clock.
import pygame
# Our settings: window size, FPS, texts, colours.
import config
# A self-check of the rules engine, run once at startup.
from engine import assert_opening
# The first screen (choose AI and seed).
from ui.setup_screen import SetupScreen
# The second screen (the actual match).
from ui.game_screen import GameScreen


# main() is called by the "if __name__ == '__main__'" block at the bottom.
# It opens the window, runs the main loop, and switches between the screens.
# It returns only when the window is closed.
def main() -> None:
    """Run the 60 FPS event loop; all engine logic remains headless-testable."""
    # Step 1: stop immediately if the board data in config.py is wrong.
    assert_opening()
    # Start all Pygame parts (video, fonts, events...).
    pygame.init()
    # Open the window. "surface" is the picture we draw on every frame.
    surface = pygame.display.set_mode(config.WINDOW_SIZE)
    # Text in the window's title bar: "Hex Reversi".
    pygame.display.set_caption(config.STRINGS["title"])
    # The clock keeps the loop at a steady 60 frames per second.
    clock = pygame.time.Clock()
    # Step 2: the app always starts on the setup screen.
    # The type hint says "screen" can hold either kind of screen.
    screen: SetupScreen | GameScreen = SetupScreen()
    # The loop keeps going while this is True.
    running = True
    # try/finally makes sure the clean-up at the bottom always runs,
    # even if an error happens inside the loop.
    try:
        # Step 3: the main loop. One repetition = one frame.
        while running:
            # 3a: handle every event that happened since the last frame.
            for event in pygame.event.get():
                # QUIT means the user clicked the window's X button.
                if event.type == pygame.QUIT:
                    running = False  # End the main loop after this frame.
                    break  # Ignore any remaining events.
                # Let the current screen react to the event.
                result = screen.handle_event(event)
                # Step 4: the setup screen returned Settings ("Start game").
                if isinstance(screen, SetupScreen) and result is not None:
                    screen = GameScreen(result)  # Switch to the match.
                # Step 6: the game screen asked for "New Setup".
                elif result == "setup":
                    screen = SetupScreen()  # Back to a fresh setup screen.
            # 3b: only the game screen has things that change over time.
            if isinstance(screen, GameScreen):
                screen.update()  # Timers, AI answers, passes, game over.
            # 3c: paint the current screen.
            screen.draw(surface)
            # Show the finished picture on the monitor.
            pygame.display.flip()
            # Wait just long enough to keep about 60 frames per second.
            clock.tick(config.FPS)
    # Step 7: this block always runs when the loop ends.
    finally:
        # A match may still have an AI thinking in the background...
        if isinstance(screen, GameScreen):
            screen.close()  # ...so tell it to stop.
        # Close the window and free Pygame's resources.
        pygame.quit()


# Python sets __name__ to "__main__" only when this file is run directly
# (python main.py). If another file imports main.py, __name__ is "main",
# this block is skipped, and no window opens by accident.
if __name__ == "__main__":
    main()  # Start the application.
