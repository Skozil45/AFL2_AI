# Hex Reversi

A Human vs AI desktop game: Reversi on a hexagon board, where tiles have
different values. The winner has the most **points**, not the most discs.

The Player is Black and moves first. The AI is White and uses Greedy or
Minimax (depth 1 to 4).

## Requirements

- Python 3.10 or newer
- pygame-ce 2.5.8 or newer (installed below)

The code uses `import pygame`, but the package is pygame-ce. If the original
`pygame` package is installed, uninstall it first, because both use the same
import name:

```bash
python -m pip uninstall pygame
```

## Install and run

Run these from this folder:

```bash
python -m pip install -r requirements.txt
```

```bash
python main.py
```

No images, sounds, fonts, or internet connection are needed.

## How to play

1. Choose Greedy or Minimax. Depth can be chosen only for Minimax.
2. Enter a whole-number seed, or leave it blank for a random one. The same seed
   always gives the same tile values.
3. Press **Start game**.
4. On your turn, click a marked tile. You have 30 seconds, or your turn is skipped.

### Controls

| Input | Action |
|---|---|
| Left click | Play a marked tile or press a button |
| Hover over a tile | Show its number, coordinates, modifier, and value |
| N | Show or hide cell numbers |
| Tab / Shift+Tab | Move the keyboard focus |
| Enter / Space | Activate the focused item |
| Backspace / Ctrl+A | Erase one character / clear the seed box |

**Restart** and **Play Again** replay the same board. **New Setup** returns to
the first screen.

## Rules

**Board:** 91 hexagon cells: 72 playable tiles and 19 fixed holes. Nobody can
play on a hole, and holes block capture lines.

**Moves:** place a disc on an empty tile so that one or more enemy discs are
trapped in a straight line between your new disc and another of yours. Lines
run in 6 directions, and every trapped disc is captured. A move must capture at
least one disc.

**Tile values:** each tile has a modifier from the seed, `+n` or `-n`, where `n`
is 1 to 5. Its value is 1 plus the modifier:

| Modifier | Value |
|---|---|
| +3 | 4 |
| -1 | 0 |
| -5 | -4 |

**Score:** the sum of the values of the tiles you own. Capturing a tile moves
its value from your opponent to you, so capturing a negative tile lowers your
score.

**End of game:** a side with no legal move is skipped. The game ends when
neither side can move, even if empty tiles remain. The higher score wins, and
equal scores are a draw.

## The AI

- **Greedy** picks the move that gives its own score the highest value. It does
  not consider the Player's reply.
- **Minimax** looks ahead 1 to 4 moves and assumes the Player replies with their
  best move. It scores positions as AI points minus Player points. Each pass uses
  one level of depth, and there is no pruning.

Ties are broken at random. The AI runs on a background thread, so the window
stays responsive while it thinks. The side panel shows the numbers behind each
decision.

## Project files

| File | Purpose |
|---|---|
| `main.py` | Starts the app and runs the main loop |
| `config.py` | Rules, sizes, colours, and all on-screen text |
| `hexgrid.py` | Hexagon coordinates and cell numbering |
| `modifiers.py` | Tile modifier values |
| `boardgen.py` | Builds the board, holes, and capture lines |
| `engine.py` | Game rules: legal moves, captures, scores, and winner |
| `ai.py` | Greedy and Minimax |
| `ui/setup_screen.py` | First screen: AI, depth, and seed |
| `ui/game_screen.py` | Game screen, timers, side panel, and AI thread |
| `ui/renderer.py` | Draws the board and finds the cell under the mouse |
| `ui/widgets.py` | Text, buttons, and keyboard focus helpers |
| `ui/gfx.py` | Screen scaling and smooth drawing |
