"""Pygame-free rules engine with cheap copies and incremental scores."""

from boardgen import Board, HOLES, PLAYABLE, RAYS, create_board
from config import (EMPTY, BLACK, WHITE, PLAYER_COLOR, BLACK_START_NUMBERS,
                    WHITE_START_NUMBERS, OPENING_MOVE_NUMBERS)
from hexgrid import CELLS


def opponent(player: int) -> int:
    """Return the other side."""
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")
    return WHITE if player == BLACK else BLACK


class GameState:
    """Mutable ownership; immutable board is shared between independent copies.

    Moves use zero-based reading-order indices. Turns do not auto-pass: callers
    must call pass_turn when needed, so Minimax can count a pass as one ply.
    """

    def __init__(self, board: Board, owners: list[int] | None = None,
                 turn: int = PLAYER_COLOR) -> None:
        opponent(turn)
        self.board = board
        self.owners = [EMPTY] * len(CELLS) if owners is None else owners.copy()
        if owners is None:
            for player, numbers in ((BLACK, BLACK_START_NUMBERS), (WHITE, WHITE_START_NUMBERS)):
                for n in numbers:
                    self.owners[n - 1] = player
        if len(self.owners) != len(CELLS) or any(p not in (EMPTY, BLACK, WHITE) for p in self.owners):
            raise ValueError("Invalid ownership list")
        if any(self.owners[i] != EMPTY for i in HOLES):
            raise ValueError("Holes cannot hold discs")
        self.turn = turn
        self.last_move: int | None = None
        self.scores = [0, self.recompute_score(BLACK), self.recompute_score(WHITE)]

    def copy(self) -> "GameState":
        """Copy only mutable fields; no RNG or full score recalculation."""
        clone = object.__new__(GameState)
        clone.board, clone.turn, clone.last_move = self.board, self.turn, self.last_move
        clone.owners, clone.scores = self.owners.copy(), self.scores.copy()
        return clone

    def flips(self, move: int, player: int | None = None) -> tuple[int, ...]:
        """Collect all bracketed opponent discs before changing any ownership."""
        player = self.turn if player is None else player
        other = opponent(player)
        if not 0 <= move < len(CELLS) or move in HOLES or self.owners[move] != EMPTY:
            return ()
        captured = []
        for ray in RAYS[move]:
            line = []
            for j in ray:
                owner = self.owners[j]
                if owner == other:
                    line.append(j)
                else:
                    if owner == player and line:
                        captured.extend(line)
                    break
        return tuple(captured)

    def legal_moves(self, player: int | None = None) -> dict[int, tuple[int, ...]]:
        """Map legal move indices to their complete flip sets."""
        moves = {}
        for move in PLAYABLE:
            if self.owners[move] == EMPTY:
                captured = self.flips(move, player)
                if captured:
                    moves[move] = captured
        return moves

    def apply_move(self, move: int) -> tuple[int, ...]:
        """Validate and commit one move, then give the turn to the other side."""
        captured = self.flips(move)
        if not captured:
            raise ValueError("Illegal move")
        self._apply_legal(move, captured)
        return captured

    def _apply_legal(self, move: int, captured: tuple[int, ...]) -> None:
        """Internal search fast path; captured must come from this state's legal_moves."""
        player, other = self.turn, opponent(self.turn)
        self.owners[move] = player
        transferred = sum(self.board.values[i] for i in captured)
        for i in captured:
            self.owners[i] = player
        self.scores[player] += self.board.values[move] + transferred
        self.scores[other] -= transferred
        self.turn, self.last_move = other, move

    def pass_turn(self) -> None:
        """Skip only a side with no move, and never pass a terminal position."""
        if self.legal_moves() or not self.legal_moves(opponent(self.turn)):
            raise ValueError("A pass is not allowed in this position")
        self.turn = opponent(self.turn)

    def forfeit_turn(self) -> None:
        """Timeout skips one turn without touching discs, scores, or pass counters."""
        self.turn = opponent(self.turn)

    def is_game_over(self) -> bool:
        """No move for either side, regardless of whether empty tiles remain."""
        return not self.legal_moves() and not self.legal_moves(opponent(self.turn))

    def score(self, player: int) -> int:
        """Current sum of the fixed values of all owned tiles."""
        return self.scores[player]

    def recompute_score(self, player: int) -> int:
        """Reference full recomputation used to verify incremental updates."""
        return sum(self.board.values[i] for i in PLAYABLE if self.owners[i] == player)

    def disc_count(self, player: int) -> int:
        """Secondary information only; never used to decide the winner."""
        return self.owners.count(player)

    def winner(self) -> int | None:
        """Return the winning color or None for a draw; only valid at game over."""
        if not self.is_game_over():
            raise ValueError("Game has not ended")
        if self.scores[BLACK] == self.scores[WHITE]:
            return None
        return BLACK if self.scores[BLACK] > self.scores[WHITE] else WHITE


def assert_opening() -> None:
    """Startup invariant for the supplied six-disc position."""
    state = GameState(create_board(0))
    assert len(CELLS) == 91 and len(PLAYABLE) == 72 and len(HOLES) == 19
    for player in (BLACK, WHITE):
        moves = state.legal_moves(player)
        assert sorted(i + 1 for i in moves) == list(OPENING_MOVE_NUMBERS)
        assert all(len(flips) == 1 for flips in moves.values())
