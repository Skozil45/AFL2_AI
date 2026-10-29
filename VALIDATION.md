# Validation record

Verified on 29 October 2026, Asia/Bangkok.

## Readability refactor verification

- **92 tests passed on both Python 3.10 and 3.12** after sharing the AI decision
  loop and simplifying move generation and numbering. The extra cases cover
  validation/cancellation for both algorithms and resetting per-decision stats.
- Repeated the **100-game experiment**: all five CSV rows matched the original
  results in every field except measured move time, including node counts.
- Compared eight deterministic Pygame renders before/after: setup, invalid seed,
  opening, numbers, AI thinking, AI result, timer warning and game over.
  All eight PNGs were byte-identical. Timing text and tie RNG were fixed for
  this comparison; it is not a new human playthrough or FPS benchmark.

## Executed checks

- **89 tests passed on Python 3.12.10**, Pygame 2.6.1, pytest 9.2.0.
- **89 tests passed on Python 3.10**, Pygame 2.6.1, pytest 9.2.0.
- `python experiments.py --games 20 --depths 1 2 3 --include-depth4` completed:
  **100 full games**, 20 per configuration, saved in `results.csv`.
- The actual native Pygame `main()` event/render loop ran for 75 frames with
  synthetic input: setup, Minimax depth 4, human move, completed AI reply,
  then a clean window close. The reply was observed in the live game controller.
- Setup, opening board and numbered-board screenshots were rendered with Pygame
  and visually inspected. Tile labels, legal markers, distinct holes/discs,
  panel text, setup fields and legend fit the 1280x800 window.

Python 3.12 emitted one upstream Pygame `pkg_resources` deprecation warning.
It did not cause a test or runtime failure. Python 3.10's test run emitted no
warnings. No Python 3.14 runtime claim is made.

## Rules and AI evidence

| Requirement | Evidence |
|---|---|
| 91 cells; numbering and exact direction order | Full round-trip, row-start and spot-check tests |
| 19 fixed holes; 72 playable; center hole | Exact set equality across seeds, point symmetry and connectivity tests |
| Fixed modifiers; exactly + and -; no zero | Seed reproducibility, range, hole exclusion, registry and example tests |
| Exact opening discs and six moves per side | Startup assertion plus independent unit test |
| All six flip directions | Six parametrized tests with multiple discs per line |
| Multi-direction flip | Simultaneous captured-set and ownership assertions |
| Illegal moves, holes, empty endpoints and edges | Targeted rejection and ray-boundary tests |
| Scores and negative values | Full recomputation after moves, opposite-order histories, negative/zero outcomes |
| Pass, full board, terminal state, draw | Targeted engine and UI integration tests |
| Timeout differs from pass | Repeated forfeits preserve discs/scores and do not cause termination |
| Greedy values points rather than flip count | Fixed seed-1 position with a uniquely better one-flip move |
| Minimax depth changes a decision | Fixed trap where depth 1 chooses #58 and depth 2 prefers #64/#66 |
| Plain exhaustive search | Independent oracle verifies evaluations and exact node counts for depths 1–4 |
| Random ties | Multiple choices across repeated equal-best positions; seeded sequence reproducibility |
| Pass consumes depth | Explicit search pass position compared to independent oracle |
| AI does not mutate input | Ownership, scores and turn compared before and after decisions |
| Full-game legality | 40 fuzz cases mixing random play, Greedy and Minimax, plus 100 experiment games |

## UI interaction evidence

The following were exercised using Pygame events and assertions under SDL's
dummy video driver. These are automated event checks, not manual clicks:

| Control/state | Observed result |
|---|---|
| Greedy/Minimax buttons | Algorithm changes; depth controls disable/enable |
| Depth 1, 2, 3, 4 | Correct depth stored |
| Invalid seed | Error shown and start rejected |
| Negative integer seed | Accepted and preserved in match settings |
| Blank seed | Produces an actual integer |
| Start / Enter in seed field | Valid settings returned |
| Ctrl+A and typed seed | Field clears and accepts replacement text |
| Tab, Shift+Tab, Enter, Space | Focus cycles; buttons/legal moves activate |
| Click hole | Ownership unchanged, illegal-move feedback shown |
| Click legal tile | Disc placement and turn change occur |
| Click board on AI turn | Ownership unchanged |
| N | Debug numbers toggle on and off |
| Restart | Same seed, same modifiers, exact initial ownership restored |
| New Setup | Navigation signal returned and worker cancelled |
| 30-second deadline | Forfeit occurs with unchanged discs/scores |
| Timer set to None | Long elapsed interval causes no forfeit |
| Real depth-4 background worker | Completes, returns legal move and statistics |
| Result arrives before 400 ms | Held until minimum visible delay expires |
| Stale result after restart | Ignored; live ownership unchanged |
| Worker failure | Visible error with restart instruction |
| No-move pass | Turn changes and skip banner appears |
| Timeout immediately followed by AI pass | Both skip messages retained; new human timer starts |
| Game over | End time freezes, overlay uses score winner/draw |
| Play Again | Same board restored and timer restarted |

## Limits

No human playthrough, macOS/Linux desktop run, screen-reader integration, or
exhaustive sustained-FPS benchmark was performed. The native smoke test used
synthetic events. Screenshots demonstrate rendered layout, not mouse hardware
or OS scaling behavior. Plain depth-4 search may take longer on other boards
and machines; the UI imposes no AI deadline.

The written style specification was used because no reference image was
attached. There are no placeholder implementations or unimplemented controls.
