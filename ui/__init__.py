"""Pygame presentation layer; the engine does not depend on this package."""

# =============================================================================
# FILE: ui/__init__.py  -  turns the "ui" folder into a Python PACKAGE.
#
# A package is a folder of Python files that can be imported together.
# Because this file exists, main.py can write:
#     from ui.setup_screen import SetupScreen
#
# The files in this package, in the order the app uses them:
#   widgets.py      - text drawing, buttons, Tab focus (used by all the others)
#   setup_screen.py - the first screen (algorithm, depth, seed)
#   game_screen.py  - the match screen (turns, timer, AI, side panel)
#   renderer.py     - draws the hex board for game_screen.py
#
# Nothing runs in this file; it only holds the description string above.
# =============================================================================
