"""Paired, timer-free comparisons against a first-moving Greedy baseline."""

import argparse
import csv
from pathlib import Path
from statistics import mean
from ai import GreedyAI, MinimaxAI
from boardgen import create_board
from config import BLACK, WHITE
from engine import GameState, assert_opening

MIN_GAMES = 20


def run_configuration(games: int, depth: int | None) -> dict[str, object]:
    """Use identical modifier seeds 1..games for each algorithm configuration."""
    wins = draws = losses = 0
    differences: list[int] = []
    timings: list[float] = []
    nodes: list[int] = []
    for seed in range(1, games + 1):
        state = GameState(create_board(seed))
        # ASSUMPTION: separate fixed tie seeds 2*s and 2*s+1 make trials reproducible.
        baseline = GreedyAI(BLACK, seed=2 * seed)
        tested = GreedyAI(WHITE, seed=2 * seed + 1) if depth is None else MinimaxAI(depth, WHITE, seed=2 * seed + 1)
        while not state.is_game_over():
            legal = state.legal_moves()
            if not legal:
                state.pass_turn()
                continue
            color = state.turn
            move, stats = (baseline if color == BLACK else tested).choose_move(state)
            assert move in legal
            if color == WHITE:
                timings.append(stats.time_ms)
                nodes.append(stats.nodes)
            state.apply_move(move)
        difference = state.score(WHITE) - state.score(BLACK)
        differences.append(difference)
        wins += difference > 0
        draws += difference == 0
        losses += difference < 0
    return {
        "algorithm": "Greedy" if depth is None else "Minimax", "depth": depth or 0,
        "games": games, "wins": wins, "draws": draws, "losses": losses,
        "win_rate_percent": round(100 * wins / games, 2),
        "average_score_difference": round(mean(differences), 3),
        "average_ai_move_ms": round(mean(timings), 3),
        "average_nodes": round(mean(nodes), 3), "ai_moves": len(timings),
        "first_player": "Player (Black), Greedy baseline", "modifier_seeds": f"1..{games}",
        "hole_layout": "fixed", "modifier_range": "-5..+5", "timer": "disabled",
    }


def main() -> None:
    """Print one row per completed configuration and save results.csv."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--games", type=int, default=MIN_GAMES)
    parser.add_argument("--depths", type=int, nargs="+", choices=(1, 2, 3), default=[1, 2, 3])
    parser.add_argument("--include-depth4", action="store_true")
    parser.add_argument("--output", type=Path, default=Path("results.csv"))
    args = parser.parse_args()
    if args.games < MIN_GAMES:
        parser.error("At least 20 games per configuration are required")
    assert_opening()
    depths = sorted(set(args.depths)) + ([4] if args.include_depth4 else [])
    print(f"Player (Black), the Greedy baseline, starts FIRST. Seeds: 1..{args.games}; fixed holes; -5..+5; no timer.", flush=True)
    print("Algorithm Depth Games Wins Draws Losses Win%  Mean AI-Player  Mean ms/move  Mean nodes", flush=True)
    with args.output.open("w", newline="", encoding="utf-8") as stream:
        writer = None
        for depth in [None] + depths:
            row = run_configuration(args.games, depth)
            if writer is None:
                writer = csv.DictWriter(stream, fieldnames=list(row))
                writer.writeheader()
            writer.writerow(row)
            stream.flush()
            print(f"{row['algorithm']:9} {row['depth']:5} {row['games']:5} {row['wins']:4} {row['draws']:5} {row['losses']:6} "
                  f"{row['win_rate_percent']:5.1f} {row['average_score_difference']:15.3f} "
                  f"{row['average_ai_move_ms']:13.3f} {row['average_nodes']:11.3f}", flush=True)
    print(f"Saved {args.output}", flush=True)


if __name__ == "__main__":
    main()
