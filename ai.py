"""Greedy and plain Minimax; no pruning, transposition cache, or timer cutoff."""

from dataclasses import dataclass
from random import Random
from threading import Event
from time import perf_counter
from config import AI_COLOR
from engine import GameState, opponent


class SearchCancelled(Exception):
    """A discarded UI match requested that its background worker stop."""


@dataclass(frozen=True)
class AIStats:
    """One decision; chosen_tile is 1-based for display."""

    chosen_tile: int
    evaluation: int
    candidates: int
    nodes: int
    time_ms: float


class GreedyAI:
    """Maximize own score after one move, breaking equal values randomly."""

    def __init__(self, color: int = AI_COLOR, seed: int | None = None,
                 cancel: Event | None = None) -> None:
        opponent(color)
        self.color, self.rng, self.cancel = color, Random(seed), cancel
        self.nodes = 0

    def _check_cancelled(self) -> None:
        if self.cancel is not None and self.cancel.is_set():
            raise SearchCancelled()

    def choose_move(self, state: GameState) -> tuple[int, AIStats]:
        """Return a legal index and stats; reject wrong-turn/no-move callers."""
        # ASSUMPTION: callers handle passes; choose_move raises if no legal move exists.
        started = perf_counter()
        state = state.copy()
        if state.turn != self.color:
            raise ValueError("AI called on the wrong turn")
        moves = state.legal_moves()
        if not moves:
            raise ValueError("No legal move; caller must pass or end the game")
        # ASSUMPTION: nodes count visited descendants (including pass nodes), not the root.
        self.nodes = 0
        evaluations = {}
        for move, flips in moves.items():
            self._check_cancelled()
            child = state.copy()
            child._apply_legal(move, flips)
            evaluations[move] = self._evaluate(child)
        best = max(evaluations.values())
        move = self.rng.choice([move for move, value in evaluations.items() if value == best])
        elapsed_ms = (perf_counter() - started) * 1000
        return move, AIStats(move + 1, best, len(moves), self.nodes, elapsed_ms)

    def _evaluate(self, state: GameState) -> int:
        """Greedy rates the board immediately after one candidate move."""
        self.nodes += 1
        return state.score(self.color)


class MinimaxAI(GreedyAI):
    """Depth counts moves and passes, including the selected root move."""

    def __init__(self, depth: int = 2, color: int = AI_COLOR, seed: int | None = None,
                 cancel: Event | None = None) -> None:
        super().__init__(color, seed, cancel)
        if depth not in (1, 2, 3, 4):
            raise ValueError("Depth must be 1..4")
        self.depth = depth

    def _evaluate(self, state: GameState) -> int:
        """The candidate move already used one level; search the remaining turns."""
        return self._search(state, self.depth - 1)

    def _search(self, state: GameState, depth: int) -> int:
        self._check_cancelled()
        self.nodes += 1
        if depth == 0:
            return state.score(self.color) - state.score(opponent(self.color))
        moves = state.legal_moves()
        if not moves:
            if not state.legal_moves(opponent(state.turn)):
                return state.score(self.color) - state.score(opponent(self.color))
            child = state.copy()
            child.turn = opponent(child.turn)
            return self._search(child, depth - 1)
        values = []
        for move, flips in moves.items():
            child = state.copy()
            child._apply_legal(move, flips)
            values.append(self._search(child, depth - 1))
        return max(values) if state.turn == self.color else min(values)
