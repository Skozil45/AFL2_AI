# Hex Reversi

A runnable Human vs AI desktop game for Python 3.10+ and pygame-ce 2.x
(Pygame Community Edition). The code still uses `import pygame`.
Black (the Player) moves first. The winner has the most **points**, not discs.
The engine, board generator, geometry, and AI import no Pygame.

## Install and run

From this directory, with Python 3.10+ and pip:

```sh
pip install -r requirements.txt
python main.py
```

Or, in a shell supporting `&&`:

```sh
pip install -r requirements.txt && python main.py
```

To clone the repository and run with Python 3.14 on Windows, use these
PowerShell commands. Install Python 3.14 first if it is not available:

```powershell
git clone https://github.com/Skozil45/AFL2_AI.git
cd AFL2_AI
py -3.14 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

If you already have the repository, open PowerShell in its root and start with
the virtual-environment command. No external images, fonts, sound files, network
service, or build step is needed after installing the dependencies.

pygame-ce provides Windows wheels for Python 3.14, avoiding the original
Pygame source-build failure. If an existing environment already has `pygame`
installed, uninstall that distribution before installing these requirements:
both distributions provide the same `pygame` import package.

```powershell
py -3.14 -m pip uninstall pygame
py -3.14 -m pip install -r requirements.txt
py -3.14 main.py
```

In a virtual environment, use its `python` for both commands instead.

## Tests and experiments

```sh
python -m pytest -q
python experiments.py --games 20 --depths 1 2 3
python experiments.py --games 20 --depths 1 2 3 --include-depth4
```

With the Windows virtual environment, replace `python` with
`.\.venv\Scripts\python.exe`. `pytest -q` also works when its executable is on PATH.
SDL's dummy drivers let the UI integration tests run without a visible window.

Experiments reject fewer than 20 games. Every configuration uses the same fixed
holes and modifier seeds `1..games`, so the default uses precisely seeds 1..20.
Greedy always occupies the first-moving Player/Black slot. The tested algorithm
occupies AI/White. A Greedy-vs-Greedy reference row is always included.
The timer and 400 ms display delay are absent from experiments.

Results are printed and saved as `results.csv` (or `--output path.csv`). A row is
flushed after each completed configuration. Win rate is `wins / games * 100`;
draws count in the denominator. Score difference is always **AI minus Player**.
Move times and node counts are averaged across the tested AI's decisions only,
not the baseline's decisions, passes, or UI delays. Every result row records the
first player, seed range, fixed hole layout, modifier range and disabled timer.

## Controls

Choose Greedy or Minimax before starting. Depth buttons 1–4 are enabled only for
Minimax. Enter an integer seed (negative integers are accepted), or leave it
blank for a random integer; the actual seed appears in the match panel.

- Click an empty tile with a small light legal-move ring to play.
- Hover a playable tile for its reading-order number, coordinates, modifier and value.
- Press **N** to toggle cell numbers on all 91 cells, including holes.
- **Tab / Shift+Tab** moves focus through controls and available legal moves.
  **Enter / Space** activates a focused button or legal move.
- In the seed field, type normally, use Backspace to erase, or Ctrl+A to clear.
  Enter submits the setup form.
- **Restart / Play Again** restores the same seed, modifiers and opening.
- **New Setup** returns to algorithm/depth/seed selection.
- Close the window to quit, including while AI search is running.

Illegal board clicks show brief feedback. Board clicks during the AI turn are
ignored; match controls remain available. A gold outline identifies the last
move. Holes never receive discs, modifiers, highlights, hover details or legal
markers. White discs have a light ring; black discs have a visible light rim;
both are smaller circles on tiles, unlike full-footprint recessed hexagonal holes.

## Rules and scoring

The board has radius 5 in axial coordinates `(q,r)`, with
`-5 <= q,r,q+r <= 5`: 91 cells, 19 fixed holes and 72 playable tiles.
Pointy-top hexes use the directions, in order:
`(1,0), (0,1), (-1,1), (-1,0), (0,-1), (1,-1)`.

Place on an empty playable tile only if at least one direction contains one or
more contiguous opponent discs followed immediately by one of your own discs.
All bracketed lines flip simultaneously. Empty tiles, holes and the board edge
break lines; there is no wrapping.

Each playable tile receives one fixed modifier, `+n` or `-n`, with `n` uniform
in 1..5 and sign selected 50/50. There is no zero modifier. Modifiers are drawn
in reading order once using `random.Random(seed)` and never change during play.
The seed affects modifiers only, never holes or opening discs.

Each tile has base value 1. `+n` means value `1+n`; `-n` means value `1-n`:

| Modifier | Calculation | Fixed tile value |
|---|---|---:|
| +3 | 1+3 | 4 |
| -2 | 1-2 | -1 |
| -1 | 1-1 | 0 |
| +5 | 1+5 | 6 |
| -5 | 1-5 | -4 |

A score is the sum of the values of **all currently owned tiles**. Values are
not chained operations on a running total. Flipping transfers the tile's fixed
value from one side to the other; taking a negative tile can lower your score.
The same ownership always yields the same score, independent of move order.
Incremental scores are tested against complete recomputation after every move.
There are exactly two registered operators, `+` and `-`, in `modifiers.py`.

If the active side has no legal move, it passes with a visible message. The game
ends only when neither side can move, including a full board. The higher final
score wins; equal scores draw regardless of disc counts.

The Player has 30 seconds per turn, resetting whenever a new Player turn starts.
Digits and a shrinking bar turn red at ten seconds. Timeout calls
`GameState.forfeit_turn()`, leaves all discs/scores unchanged, and gives the turn
to AI. It does not increment a pass counter or itself end the game. Normal
no-move/game-over rules still apply to the resulting position. AI has no deadline;
its thinking time is shown. Both clocks stop at game over. Set
`TURN_TIME_LIMIT_SECONDS = None` in `config.py` to disable the human timer.

## Reading order, holes and opening

Rows are read top to bottom, and q increases left to right within a row.

| r | q range | Cell numbers | Fixed hole numbers |
|---:|---|---|---|
| -5 | 0..5 | 1–6 | none |
| -4 | -1..5 | 7–13 | 8, 10, 12 |
| -3 | -2..5 | 14–21 | none |
| -2 | -3..5 | 22–30 | 23, 25, 27, 29 |
| -1 | -4..5 | 31–40 | none |
| 0 | -5..5 | 41–51 | 42, 44, 46, 48, 50 |
| 1 | -5..4 | 52–61 | none |
| 2 | -5..3 | 62–70 | 63, 65, 67, 69 |
| 3 | -5..2 | 71–78 | none |
| 4 | -5..1 | 79–85 | 80, 82, 84 |
| 5 | -5..0 | 86–91 | none |

`cell_number(q,r) = row_start + (q - q_min)` and `cell_from_number(n)` are in
`hexgrid.py`. In particular #1=(0,-5), #35=(0,-1), #46=(0,0), #84=(0,4),
#91=(0,5). The center is a hole. The hole set is point-symmetric and the playable
region is connected. There is no hole randomization or repair code.

| Side | Starting numbers | Axial coordinates |
|---|---|---|
| White / AI | 35, 47, 56 | (0,-1), (1,0), (-1,1) |
| Black / Player | 36, 45, 57 | (1,-1), (-1,0), (0,1) |

Both sides initially have exactly six legal moves:
#26=(1,-2), #34=(-1,-1), #37=(2,-1), #55=(-2,1), #58=(1,1), #66=(-1,2).
Each flips exactly one disc. Startup and unit tests assert these invariants.

## AI and computational cost

`choose_move(state)` returns `(zero_based_move_index, AIStats)`. Statistics contain
the 1-based chosen tile, evaluation, candidate count b, visited nodes and decision
milliseconds measured with `time.perf_counter`. Calls copy the input state and
never mutate the live game. Each AI owns an independent `random.Random` for ties.

Both algorithms share `GreedyAI.choose_move`: validate the turn, simulate each
legal move, evaluate each resulting board, then randomly choose a best move.
Only `_evaluate` differs. Greedy returns its own score immediately; Minimax
overrides `_evaluate` to call `_search` for the remaining depth. Timing,
tie-breaking, cancellation and statistics are handled in one place.

**Greedy** simulates every legal candidate and maximizes its own resulting score.
Its reported evaluation is its own score, not score difference. The experiment's
Black baseline applies this same rule from Black's perspective.

**Minimax** evaluates every root move to a depth of 1–4. AI maximizes and Player
minimizes. Leaves and terminal states evaluate `score(AI)-score(Player)`. A pass
consumes one depth level. Terminal positions can end before the requested depth.
Equal best root candidates are selected randomly. There is no alpha-beta pruning,
transposition table, heuristic move removal, or time-based search cutoff.

For fixed board size, Greedy considers **O(b)** candidates and plain Minimax
visits **O(b^d)** nodes. Real branching changes by position and a pass has one
successor, so measured counts need not equal a literal b^d. With board size
treated as variable, move generation, copying and evaluation add their board-scan
cost; b and d alone suppress that fixed 91-cell factor. Search copies share
immutable modifiers/values/rays and copy only flat ownership/score lists.
The recursive search stores one level's children values at a time; it does not
materialize a complete search tree.

The UI searches on a daemon background thread. Only the main thread calls
Pygame or mutates the live state. A cancellation event and match-generation
number prevent results from old matches being applied after Restart/New Setup.
The main loop targets 60 FPS; thread scheduling and machine speed can affect
actual FPS. The visible thinking phase lasts at least 400 ms. Decision-time
statistics exclude this extra display delay. Unexpected worker errors are shown
with a restart instruction instead of silently freezing the match.

## Measured experiments

This is also the table to replace/paste new experiment results into. These are
actual results from `results.csv`: 20 games per configuration, modifier seeds
1..20, fixed tie seeds, first-moving Greedy/Black baseline. Python 3.12.10,
Windows, one local run. Times depend on the machine and background activity.

| Tested AI | Depth | Wins | Draws | Losses | Win rate | Mean AI-Player | Mean ms / AI move | Mean nodes / AI move |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Greedy | n/a | 8 | 0 | 12 | 40% | -14.20 | 0.028 | 4.041 |
| Minimax | 1 | 5 | 1 | 14 | 25% | -12.05 | 0.029 | 3.947 |
| Minimax | 2 | 17 | 0 | 3 | 85% | 30.30 | 0.152 | 22.101 |
| Minimax | 3 | 13 | 0 | 7 | 65% | 18.20 | 0.781 | 129.523 |
| Minimax | 4 | 14 | 0 | 6 | 70% | 26.10 | 3.627 | 589.220 |

This sample shows growing search cost, but not monotonically improving wins.
Depth-limited score difference has horizon effects, and this is only 20 boards
against one fixed first-moving baseline. These results are not a general ranking
against humans, other opponents, or all possible modifier assignments.

## PEAS analysis

| PEAS component | Hex Reversi |
|---|---|
| Performance measure | Final score difference, win rate, move validity, AI response time |
| Environment | 72 tiles plus 19 fixed hex holes; two players; modifiers fixed per match; alternating turns and six-direction flipping |
| Actuators | AI selects a legal tile; engine places/flips discs and updates scores; UI displays the result |
| Sensors | All tile states, modifier signs and numbers, disc ownership, active turn and legal moves |

Environment properties: **fully observable**, **deterministic after the initial
modifier randomization**, **sequential**, **static during AI computation**,
**discrete**, **multi-agent**, **competitive**, and **turn-based with a 30 s human
timer**. Random tie-breaking is an agent policy choice, not stochastic board
transition dynamics. The clock display advances during search, but ownership
and modifiers are static while that decision is computed.

## Inputs and outputs

| Category | Data |
|---|---|
| Inputs | Greedy/Minimax choice; Minimax depth; optional integer seed; Player's tile clicks (or keyboard selection) |
| Fixed | Hole layout; modifier range -5..+5; base value 1; starting discs; Player moves first |
| Outputs | Hex board with signed modifiers; legal-move markers; ownership and score changes each turn; chosen AI move and search statistics; pass/timeout messages; timers; final scores and winner/draw |

## Four project questions

1. **How does six-direction flipping work on a hex board?**
   `hexgrid.py:DIRECTIONS/NEIGHBORS`, `boardgen.py:RAYS` and
   `engine.py:GameState.flips` collect every bracketed line before mutation.
   `tests/test_engine.py` tests six directions separately, multiple discs and
   multiple directions. With this exact parity hole layout a hole is either
   immediately adjacent along a ray or absent from that ray, so tests check
   adjacent-hole blocking and ensure no precomputed ray ever crosses a hole.
2. **How is modifier scoring kept consistent?**
   `modifiers.py:OPERATORS/tile_value`, `boardgen.py:create_board` and
   `engine.py:_apply_legal/recompute_score`. Tests compare cached scores against
   recomputation every turn, verify negative/zero tiles, and play independent
   moves in opposite orders to obtain identical ownership and scores.
3. **How do Greedy and Minimax choose differently?**
   `ai.py` contains both implementations. Greedy maximizes own points; Minimax
   evaluates score difference after replies. The fixed test positions in
   `tests/test_ai.py` prove that the most flips need not give the best Greedy
   move, and that depth 1 takes #58 while depth 2 prefers #64/#66 in a trap.
4. **How does depth affect decision quality and cost?**
   `experiments.py` and `results.csv` compare paired seeds and report wins,
   score differences, time and nodes. `test_minimax_matches_exhaustive_oracle`
   verifies values and node counts at depths 1–4 against a separate rules-based
   recursive oracle. See the measured table and complexity discussion above.

## File map

| File | Responsibility |
|---|---|
| `main.py` | Startup assertion and 60 FPS screen/event loop |
| `config.py` | Rules, colors, UI constants and the single `STRINGS` translation dictionary |
| `hexgrid.py` | Axial coordinates, numbering, neighbor indices and cube-rounded hit testing |
| `boardgen.py` | Fixed holes, precomputed rays and immutable seeded board values |
| `modifiers.py` | Exactly two operators and validated tile values |
| `engine.py` | Ownership, legal moves, flips, passes, forfeits, scores and winner |
| `ai.py` | Greedy/Minimax, isolated tie RNG, cancellation and statistics |
| `ui/widgets.py` | Text, wrapping, buttons and focus helpers |
| `ui/setup_screen.py` | Algorithm/depth/seed setup and validation |
| `ui/renderer.py` | Board, discs, holes, markers, hover information and legend |
| `ui/game_screen.py` | Thread coordination, timers, input and result overlay |
| `experiments.py` | Headless paired comparisons, console table and CSV |
| `tests/` | Geometry, modifiers, engine, AI, fuzz and UI integration coverage |
| `VALIDATION.md` | Checks performed and remaining limits |

For a short code presentation, follow one move in this order:

1. `main.py` starts setup and switches to the game screen.
2. `boardgen.py` builds the fixed board and draws seeded modifiers. A **ray**
   is the precomputed list of tiles in one direction, stopping before a hole/edge.
3. `engine.py:flips` checks those rays. `legal_moves` keeps moves that capture;
   `apply_move` validates a move and `_apply_legal` places, flips and transfers points.
4. `ai.py:choose_move` tries the same moves on copies. `_evaluate` supplies the
   Greedy score or Minimax result; `_search` alternates maximizing and minimizing.
5. `ui/game_screen.py` handles clicks, deadlines and completed AI results.
   `ui/renderer.py` draws the resulting state; it does not decide the game rules.

To translate the UI, edit `config.STRINGS`. Numeric modifier signs, cell numbers
and generated values remain data. Experiment CLI messages are separate from
the Pygame interface. Keep format fields such as `{score}` intact.

## Assumptions

Each implementation assumption is marked by an `ASSUMPTION:` comment at its
point of use:

1. **Player = Black**, following Othello's first-mover convention (`config.py`).
2. **-5..+5 is the signed modifier range, with no zero modifier**; base 1 gives
   tile values -4..+6 (`config.py`).
3. **The timer is enforced only on the human Player**; AI turns are not
   time-limited (`config.py`).
4. **Red warning begins at 10 seconds remaining** (`config.py`).
5. A **fixed 1280x800 desktop window**, Pygame's built-in font and drawn geometry
   are used; there are no external artwork/audio dependencies (`config.py`).
   No reference image was attached, so the supplied written palette and geometry
   define the visual implementation.
6. Setup defaults to **Greedy**, with **depth 2** initially selected when Minimax
   is enabled (`ui/setup_screen.py`).
7. UI tie-breaking has its own **unseeded RNG**; restarting restores the board
   but need not replay identical ties (`ui/game_screen.py`).
8. Experiments use separate reproducible tie seeds **2*s for Black and 2*s+1 for
   White**, where s is the board seed (`experiments.py`).
9. Node counts include **visited descendants and pass nodes, excluding the root**
   (`ai.py`). Greedy counts evaluated candidate boards.
10. A **one-pixel shadow** beneath light empty-tile labels improves readability
    on the requested tile tints (`ui/renderer.py`).
11. `choose_move` is called only when its side has a legal move; **no-move calls
    raise ValueError**, and callers perform the pass or end the game (`ai.py`).

## Verification limits

See `VALIDATION.md` for concrete checks. Automated event tests and rendered
screenshots do not constitute a human playthrough. No claim of constant 60 FPS
on all computers is made; plain depth-4 Minimax is intentionally unpruned.
