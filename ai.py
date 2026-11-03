"""Greedy and plain Minimax; no pruning, transposition cache, or timer cutoff."""

# =============================================================================
# FILE: ai.py  -  the two computer players.
#
# -----------------------------------------------------------------------------
# CONCEPT: GREEDY
# -----------------------------------------------------------------------------
# Greedy tries every legal move and picks the one that gives the AI the
# most points RIGHT AFTER that move. It never thinks about your reply, so
# it is fast but easy to trick.
#
# -----------------------------------------------------------------------------
# CONCEPT: MINIMAX
# -----------------------------------------------------------------------------
# Minimax also thinks about your replies. It imagines the game a few moves
# ahead and assumes BOTH sides play their best:
#   - on the AI's turn it picks the MAXIMUM score (best for the AI)
#   - on your turn it expects the MINIMUM score (worst for the AI)
# The score it uses is (AI points - your points).
#
# A tiny example with depth 2 (AI move, then your reply):
#
#                       AI to move
#                      /          \
#                 AI plays A    AI plays B
#                 /      \       /      \
#      you reply: +3     -4     +1      +2     <- score after your reply
#
#   If the AI plays A, you will pick -4 (worst for the AI), so A is worth -4.
#   If the AI plays B, you will pick +1, so B is worth +1.
#   The AI picks B, the maximum of -4 and +1.
#
# A "PLY" is one turn by one side. Depth 2 = the AI's move plus your reply.
# Here a pass also counts as one ply. A higher depth plays better, but each
# extra ply multiplies the work by roughly the number of legal moves.
#
# A "NODE" is one position the AI looks at. AIStats.nodes counts them.
#
# -----------------------------------------------------------------------------
# HOW THIS FILE IS USED
# -----------------------------------------------------------------------------
# GameScreen.launch_ai() starts a background thread that calls
# ai.choose_move(copy of the game). choose_move() returns the chosen move
# and an AIStats, which the side panel shows under "Last AI decision".
# If you press Restart or New Setup while the AI is thinking, the game
# screen sets the "cancel" flag. The AI notices it in _check_cancelled()
# and raises SearchCancelled, which ends the thread quietly.
# =============================================================================

# dataclass writes the __init__ method of AIStats for us.
from dataclasses import dataclass
# Random choice between moves that are equally good.
from random import Random
# An on/off flag that can be shared safely between threads.
from threading import Event
# A precise clock, used to measure how long the AI thinks.
from time import perf_counter
# The AI plays White by default.
from config import AI_COLOR
# The game rules.
from engine import GameState, opponent


# A custom error used to stop a search early. It is raised when the match
# was restarted or left; GameScreen catches it and ignores it.
class SearchCancelled(Exception):
    """A discarded UI match requested that its background worker stop."""


# The statistics of one AI decision, shown in the side panel.
@dataclass(frozen=True)
class AIStats:
    """One decision; chosen_tile is 1-based for display."""

    # The number (1 to 91) of the chosen tile.
    chosen_tile: int
    # The score the AI expected from that move.
    evaluation: int
    # How many legal moves the AI could choose from ("b" = branching factor).
    candidates: int
    # How many positions the AI examined.
    nodes: int
    # How long the decision took, in milliseconds.
    time_ms: float


# The Greedy player. Created by GameScreen.restart() when you choose Greedy.
# MinimaxAI below is built on top of this class.
class GreedyAI:
    """Maximize own score after one move, breaking equal values randomly."""

    # seed=None means ties are broken unpredictably.
    # cancel is the flag the game screen uses to stop the search.
    def __init__(self, color: int = AI_COLOR, seed: int | None = None,
                 cancel: Event | None = None) -> None:
        # Check that color is BLACK or WHITE.
        opponent(color)
        # Which side we play, our random generator, and the cancel flag.
        self.color, self.rng, self.cancel = color, Random(seed), cancel
        # Counts the positions examined; reset for every decision.
        self.nodes = 0

    # Stops the search if the game screen raised the cancel flag.
    # Called before each move is tried, and at every Minimax position.
    def _check_cancelled(self) -> None:
        if self.cancel is not None and self.cancel.is_set():
            raise SearchCancelled()

    # Chooses a move. Runs in the background thread started by
    # GameScreen.launch_ai(). Both AIs use this method: try every legal move,
    # score it with _evaluate(), and keep the best one.
    def choose_move(self, state: GameState) -> tuple[int, AIStats]:
        """Return a legal index and stats; reject wrong-turn/no-move callers."""
        # ASSUMPTION: callers handle passes; choose_move raises if no legal move exists.
        # Start the stopwatch.
        started = perf_counter()
        # Work on our own copy, so the real game is never changed.
        state = state.copy()
        # It must be our turn.
        if state.turn != self.color:
            raise ValueError("AI called on the wrong turn")
        # Our legal moves, as {move: captured discs}.
        moves = state.legal_moves()
        # With no legal move the game screen should have passed instead.
        if not moves:
            raise ValueError("No legal move; caller must pass or end the game")
        # ASSUMPTION: nodes count visited descendants (including pass nodes), not the root.
        self.nodes = 0
        # The score of every move we try: {move: score}.
        evaluations = {}
        # Try every legal move.
        for move, flips in moves.items():
            # Stop early if the match was discarded.
            self._check_cancelled()
            # Play the move on a copy...
            child = state.copy()
            child._apply_legal(move, flips)
            # ...and score the result (Greedy and Minimax do this differently).
            evaluations[move] = self._evaluate(child)
        # The best score we found.
        best = max(evaluations.values())
        # Several moves may share the best score; pick one of them at random.
        move = self.rng.choice([move for move, value in evaluations.items() if value == best])
        # Stop the stopwatch and convert seconds to milliseconds.
        elapsed_ms = (perf_counter() - started) * 1000
        # Return the move and the statistics for the side panel.
        return move, AIStats(move + 1, best, len(moves), self.nodes, elapsed_ms)

    # Scores the position after one move. Greedy's version: the AI's points.
    # MinimaxAI replaces this method with a deeper search.
    def _evaluate(self, state: GameState) -> int:
        """Greedy rates the board immediately after one candidate move."""
        # One more position examined.
        self.nodes += 1
        # More points is better for the AI.
        return state.score(self.color)


# The Minimax player. Created by GameScreen.restart() when you choose Minimax.
# "MinimaxAI(GreedyAI)" means it INHERITS everything from GreedyAI, including
# choose_move(), and only replaces _evaluate().
class MinimaxAI(GreedyAI):
    """Depth counts moves and passes, including the selected root move."""

    # depth comes from the setup screen (1 to 4).
    def __init__(self, depth: int = 2, color: int = AI_COLOR, seed: int | None = None,
                 cancel: Event | None = None) -> None:
        # Run GreedyAI's __init__ first (color, random generator, cancel flag).
        super().__init__(color, seed, cancel)
        # Only the depths offered on the setup screen are allowed.
        if depth not in (1, 2, 3, 4):
            raise ValueError("Depth must be 1..4")
        # How many plies to look ahead in total.
        self.depth = depth

    # Replaces Greedy's _evaluate(). The move tried in choose_move() already
    # used one ply, so the search continues with depth - 1.
    def _evaluate(self, state: GameState) -> int:
        """The candidate move already used one level; search the remaining turns."""
        return self._search(state, self.depth - 1)

    # The Minimax search (see the example at the top of this file).
    # It is RECURSIVE: it calls itself for every possible next move, with one
    # less ply each time, until depth reaches 0 or the game ends.
    # Returns (AI points - your points), assuming both sides play their best.
    def _search(self, state: GameState, depth: int) -> int:
        # Stop quickly if the match was discarded.
        self._check_cancelled()
        # One more position examined.
        self.nodes += 1
        # No plies left: just score this position.
        if depth == 0:
            return state.score(self.color) - state.score(opponent(self.color))
        # The legal moves of the side to move in this imagined position.
        moves = state.legal_moves()
        # This side cannot move...
        if not moves:
            # ...and neither can the other side: the game is over here.
            if not state.legal_moves(opponent(state.turn)):
                return state.score(self.color) - state.score(opponent(self.color))
            # Otherwise this side passes: same discs, other side to move.
            child = state.copy()
            child.turn = opponent(child.turn)
            # The pass uses up one ply.
            return self._search(child, depth - 1)
        # The score of every possible move from here.
        values = []
        for move, flips in moves.items():
            # Play the move on a copy...
            child = state.copy()
            child._apply_legal(move, flips)
            # ...and look deeper from there (the function calls itself).
            values.append(self._search(child, depth - 1))
        # The AI picks the best score for itself; you are expected to pick
        # the worst score for the AI.
        return max(values) if state.turn == self.color else min(values)
