"""Rules, presentation constants, and all translatable interface text."""

RADIUS = 5
DIRECTIONS = ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))
HOLE_NUMBERS = (8, 10, 12, 23, 25, 27, 29, 42, 44, 46, 48, 50, 63, 65, 67, 69, 80, 82, 84)
WHITE_START_NUMBERS = (35, 47, 56)
BLACK_START_NUMBERS = (36, 45, 57)
OPENING_MOVE_NUMBERS = (26, 34, 37, 55, 58, 66)
EMPTY, BLACK, WHITE = 0, 1, 2
# ASSUMPTION: Player is Black, following Othello's first-mover convention.
PLAYER_COLOR, AI_COLOR = BLACK, WHITE
BASE_VALUE = 1
# ASSUMPTION: -5..+5 denotes signed modifiers, with no zero; values are -4..+6.
MODIFIER_MIN_N, MODIFIER_MAX_N = 1, 5
# ASSUMPTION: only human turns are limited; AI turns have no time limit.
TURN_TIME_LIMIT_SECONDS = 30
# ASSUMPTION: the warning starts at ten seconds remaining.
TIMER_WARNING_SECONDS = 10
AI_MIN_DELAY_SECONDS = 0.4
FPS = 60
WINDOW_SIZE = (1280, 800)
# ASSUMPTION: fixed-size desktop window, built-in font, no external artwork/audio.
FONT_NAME = None
FONT_SMALL, FONT_BODY, FONT_HEADING, FONT_TITLE = 19, 25, 34, 56
DISC_RADIUS_RATIO = 0.62
BANNER_SECONDS = 4.0
SEED_BITS = 32
COLORS = {
    "background": "#1b1b1b", "plate": "#335c3f", "wood": "#4a3626",
    "positive": "#4a8a5e", "negative": "#8b6a4e", "tile_edge": "#3b6f4b",
    "hole": "#101113", "hole_edge": "#2c2e31", "white": "#f4f3ee",
    "black": "#1e1e1c", "rim": "#c4c6c2", "inner": "#666963",
    "text": "#ffffff", "muted": "#c2c6be", "gold": "#e6bd65",
    "panel": "#252824", "button": "#3c5140", "disabled": "#343634",
    "red": "#ff827a", "shadow": "#16241a",
}
STRINGS = {
    "title": "Hex Reversi", "subtitle": "Win points, not just pieces.",
    "algorithm": "AI algorithm", "greedy": "Greedy",
    "minimax": "Minimax", "depth": "Search depth", "depth_number": "{depth}",
    "depth_note": "Depth 4 may be slow. Plain Minimax, no pruning.",
    "seed_label": "Seed (blank = random)", "seed_error": "Enter a whole number or leave the seed blank.",
    "holes_info": "Hole layout: fixed", "range_info": "Modifier range: -5 to +5",
    "limit_info": "Turn time limit: {limit} s", "limit_off": "Turn time limit: disabled",
    "start": "Start game", "restart": "Restart", "new_setup": "New Setup",
    "again": "Play Again", "player": "Player (Black)", "ai": "AI (White)",
    "player_short": "Player", "ai_short": "AI", "player_turn": "Your turn",
    "thinking": "AI is thinking...", "over": "Game over", "draw": "Draw",
    "winner": "{name} wins", "score": "{name}: {score} points",
    "discs": "Discs: Player {black} / AI {white}", "difference": "AI - Player: {difference:+d}",
    "seed": "Seed: {seed}", "config": "{algorithm} / depth {depth}", "na": "-",
    "elapsed": "Game time: {seconds:.1f} s", "remaining": "Your time: {seconds:.1f} s",
    "ai_time": "Thinking time: {seconds:.1f} s", "timer_stopped": "Turn timer stopped",
    "timeout": "Time's up - Player's turn skipped", "pass": "{name} has no legal moves - turn skipped",
    "combined_banner": "{first}\n{second}",
    "illegal": "Choose an empty marked tile.", "hover": "#{number}  ({q}, {r})   {modifier}   value {value:+d}",
    "hover_hint": "Hover a tile for its value. N: cell numbers.", "number": "{number}",
    "ai_info": "Last AI decision", "no_decision": "No AI move yet.",
    "chosen": "Chosen tile: #{number}", "evaluation": "Evaluation: {value:+d}",
    "candidates": "Candidates (b): {count}", "nodes": "Nodes evaluated: {count:,}",
    "decision_time": "Decision time: {ms:.2f} ms", "ai_error": "AI failed: {error}. Restart to retry.",
    "white_piece": "White piece", "black_piece": "Black piece", "hole": "Hole",
    "empty_cell": "Empty cell", "plus": "+ tile", "minus": "- tile",
    "keys": "Tab: focus   Enter: select   N: numbers",
}
