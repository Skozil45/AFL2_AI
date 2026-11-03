"""Rules, presentation constants, and all translatable interface text."""

# =============================================================================
# FILE: config.py  -  every fixed number, colour and text used by the app.
#
# This file has no functions. It only defines CONSTANTS (values that never
# change while the program runs). By convention, constants are written in
# CAPITAL_LETTERS. Other files read them:
#   - hexgrid.py, boardgen.py, engine.py, modifiers.py use the RULE values.
#   - ai.py uses AI_COLOR.
#   - main.py and the ui/ files use the window, timing, font, colour and
#     text values.
# Changing a value here changes the whole game, without touching any logic.
#
# CELL NUMBERS: cells are numbered 1 to 91 in reading order: the top row
# from left to right, then the next row, and so on (like reading a book).
# =============================================================================

# ---- Board and rules --------------------------------------------------------

# The board is a big hexagon with 5 rings of cells around the centre cell.
# That gives 1 + 6 + 12 + 18 + 24 + 30 = 91 cells.
RADIUS = 5
# The 6 steps (dq, dr) from a hex to each of its 6 neighbours.
# See hexgrid.py for what q and r mean.
DIRECTIONS = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))
# The 19 cells that are holes: nobody can play there, and they block lines.
HOLE_NUMBERS = (8, 10, 12, 23, 25, 27, 29, 42, 44, 46,
                48, 50, 63, 65, 67, 69, 80, 82, 84)
# Cells that hold a White disc at the start of the game.
WHITE_START_NUMBERS = (35, 47, 56)
# Cells that hold a Black disc at the start of the game.
BLACK_START_NUMBERS = (36, 45, 57)
# The legal first moves we expect. engine.assert_opening() checks this.
OPENING_MOVE_NUMBERS = (26, 34, 37, 55, 58, 66)
# What each cell can contain. The same numbers also identify the players.
EMPTY, BLACK, WHITE = 0, 1, 2
# ASSUMPTION: Player is Black, following Othello's first-mover convention.
# The human plays Black and moves first; the AI plays White.
PLAYER_COLOR, AI_COLOR = BLACK, WHITE
# Every tile is worth 1 point before its modifier is applied.
BASE_VALUE = 1
# ASSUMPTION: -5..+5 denotes signed modifiers, with no zero; values are -4..+6.
# A modifier is "+n" or "-n" with n from 1 to 5.
# So a tile is worth 1 + n (2 to 6) or 1 - n (0 to -4).
MODIFIER_MIN_N, MODIFIER_MAX_N = 1, 5

# ---- Timing -----------------------------------------------------------------

# ASSUMPTION: only human turns are limited; AI turns have no time limit.
# The human must move within 30 seconds, or the turn is skipped.
# Setting this to None turns the limit off.
TURN_TIME_LIMIT_SECONDS = 30
# ASSUMPTION: the warning starts at ten seconds remaining.
# The timer turns red when this many seconds are left.
TIMER_WARNING_SECONDS = 10
# The AI always waits at least this long before moving, so you can see
# "AI is thinking..." even when it decides instantly.
AI_MIN_DELAY_SECONDS = 0.4
# Frames per second of the main loop in main.py.
FPS = 60

# ---- Window and drawing -----------------------------------------------------

# Window width and height in pixels. The screen layouts are designed
# for exactly this size.
WINDOW_SIZE = (1280, 800)
# ASSUMPTION: fixed-size desktop window, built-in font, no external artwork/audio.
# None means "use Pygame's built-in font".
FONT_NAME = None
# Font sizes in pixels.
FONT_SMALL, FONT_BODY, FONT_HEADING, FONT_TITLE = 19, 25, 34, 56
# A disc's radius as a fraction of a hex's size (0.62 = 62%).
DISC_RADIUS_RATIO = 0.62
# How many seconds a message (pass, timeout, illegal move) stays visible.
BANNER_SECONDS = 4.0
# A blank seed becomes a random 32-bit number (see setup_screen.py).
SEED_BITS = 32
# Named colours as "#RRGGBB" codes. Drawing code uses COLORS["name"].
COLORS = {
    # Window background, board plate, wooden board frame.
    "background": "#1b1b1b", "plate": "#335c3f", "wood": "#4a3626",
    # "+" tile, "-" tile, tile outline.
    "positive": "#4a8a5e", "negative": "#8b6a4e", "tile_edge": "#3b6f4b",
    # Hole fill, hole outline, White disc.
    "hole": "#101113", "hole_edge": "#2c2e31", "white": "#f4f3ee",
    # Black disc, disc rim and hover outline, inner ring of a Black disc.
    "black": "#1e1e1c", "rim": "#c4c6c2", "inner": "#666963",
    # Normal text, less important text, highlight and keyboard focus.
    "text": "#ffffff", "muted": "#c2c6be", "gold": "#e6bd65",
    # Side panel, button, disabled button.
    "panel": "#252824", "button": "#3c5140", "disabled": "#343634",
    # Errors and low timer, disc shadow.
    "red": "#ff827a", "shadow": "#16241a",
}

# ---- All interface text -----------------------------------------------------

# Every piece of text on screen. Code reads it with ui.widgets.tr(key, ...),
# which fills in the {placeholders}. For example:
#     tr("score", name="AI", score=5)  ->  "AI: 5 points"
# Inside braces, ":+d" means "whole number with a + or - sign",
# ":.1f" means "one digit after the decimal point", and ":," adds
# thousands separators (12,345).
# To translate the game, change only the texts on the right.
STRINGS = {
    # Window and screen title; setup screen subtitle.
    "title": "Hex Reversi", "subtitle": "Win points, not just pieces.",
    # Setup screen: algorithm label and the Greedy button.
    "algorithm": "AI algorithm", "greedy": "Greedy",
    # Setup screen: Minimax button, depth label, text on each depth button.
    "minimax": "Minimax", "depth": "Search depth", "depth_number": "{depth}",
    # Setup screen: hint under the depth buttons.
    "depth_note": "Search depth is how smart the enemy is, higher = harder.",
    # Setup screen: seed box label, and the error for an invalid seed.
    "seed_label": "Seed (blank = random)",
    "seed_error": "Enter a whole number or leave the seed blank.",
    # Fixed rule information.
    "holes_info": "Hole layout: fixed", "range_info": "Modifier range: -5 to +5",
    # Turn timer information.
    "limit_info": "Turn time limit: {limit} s", "limit_off": "Turn time limit: disabled",
    # Button labels.
    "start": "Start game", "restart": "Restart", "new_setup": "New Setup",
    # Game-over button, and the names of the two sides.
    "again": "Play Again", "player": "Player (Black)", "ai": "AI (White)",
    # Short side names, and the side panel heading on your turn.
    "player_short": "Player", "ai_short": "AI", "player_turn": "Your turn",
    # Other side panel headings, and the result text for a draw.
    "thinking": "AI is thinking...", "over": "Game over", "draw": "Draw",
    # Game-over title, and one score line.
    "winner": "{name} wins", "score": "{name}: {score} points",
    # Disc count line, and the score difference line.
    "discs": "Discs: Player {black} / AI {white}",
    "difference": "AI - Player: {difference:+d}",
    # Side panel: seed, AI settings, and "-" for "not applicable".
    "seed": "Seed: {seed}", "config": "{algorithm} / depth {depth}", "na": "-",
    # Side panel: total game time, and your remaining turn time.
    "elapsed": "Game time: {seconds:.1f} s", "remaining": "Your time: {seconds:.1f} s",
    # Side panel: how long the AI has been thinking; text after game over.
    "ai_time": "Thinking time: {seconds:.1f} s", "timer_stopped": "Turn timer stopped",
    # Message when your time runs out.
    "timeout": "Time's up - Player's turn skipped",
    # Message when a side has no legal move.
    "pass": "{name} has no legal moves - turn skipped",
    # Two messages shown together, one per line ("\n" is a line break).
    "combined_banner": "{first}\n{second}",
    # Message after clicking a tile that is not a legal move.
    "illegal": "Choose an empty marked tile.",
    # Info line about the tile under the mouse.
    "hover": "#{number}  ({q}, {r})   {modifier}   value {value:+d}",
    # Info line when the mouse is not over a tile; text of a cell number.
    "hover_hint": "Hover a tile for its value. N: cell numbers.", "number": "{number}",
    # Side panel: heading of the AI statistics, and text before the AI's first move.
    "ai_info": "Last AI decision", "no_decision": "No AI move yet.",
    # AI statistics: the chosen tile and the score the AI expected.
    "chosen": "Chosen tile: #{number}", "evaluation": "Evaluation: {value:+d}",
    # AI statistics: number of legal moves, and positions examined.
    "candidates": "Candidates (b): {count}", "nodes": "Nodes evaluated: {count:,}",
    # AI statistics: thinking time in milliseconds.
    "decision_time": "Decision time: {ms:.2f} ms",
    # Message if the AI crashes.
    "ai_error": "AI failed: {error}. Restart to retry.",
    # Legend labels under the board.
    "white_piece": "White piece", "black_piece": "Black piece", "hole": "Hole",
    "empty_cell": "Empty cell", "plus": "+ tile", "minus": "- tile",
    # Keyboard help at the bottom of the setup screen.
    "keys": "Tab: focus   Enter: select   N: numbers",
}
