"""Pygame-free rules engine with cheap copies and incremental scores."""

# =============================================================================
# FILE: engine.py  -  the game rules (no drawing, no Pygame).
#
# A GameState is one moment of the game: who owns each cell, whose turn it
# is, and both scores.
#
# -----------------------------------------------------------------------------
# CONCEPT: HOW A CAPTURE WORKS  (the Reversi / Othello rule)
# -----------------------------------------------------------------------------
# You place a disc on an empty cell X. Then, in each of the 6 directions,
# look along the straight line:
#
#     X  W  W  B     -> the two W discs are trapped between your new disc
#                       and your own disc B, so both become yours.
#     X  W  W  .     -> the line ends at an empty cell: nothing is captured.
#     X  W  W  #     -> the line ends at a hole (#): nothing is captured.
#     X  B           -> no opponent disc in between: nothing is captured.
#
# (Here you are Black, B; W is White.) A move is LEGAL only if it captures
# at least one disc in some direction. If a side has no legal move, it must
# PASS. When NEITHER side can move, the game is over.
#
# -----------------------------------------------------------------------------
# CONCEPT: SCORE
# -----------------------------------------------------------------------------
# Your score is the total point value of the tiles you own, NOT the number
# of discs. A capture moves the points of the captured tiles from the
# opponent to you.
#
# Who uses this file:
#   - main.py: assert_opening() once at startup
#   - ui/game_screen.py: creates the real GameState and plays the moves
#   - ai.py: copies GameStates to try moves "in its head"
#
# The flow of one move:
#   legal_moves()   -> calls flips() for every empty cell to find captures
#   apply_move(x)   -> calls flips() again to check the move is legal, then
#   _apply_legal()  -> places the disc, flips the captured discs, updates
#                      both scores, and gives the turn to the other side
# =============================================================================

# The fixed board data, and the function that builds a board.
from boardgen import Board, HOLES, PLAYABLE, RAYS, create_board
# Cell and player values, who moves first, and the start position.
from config import (EMPTY, BLACK, WHITE, PLAYER_COLOR, BLACK_START_NUMBERS,
                    WHITE_START_NUMBERS, OPENING_MOVE_NUMBERS)
# The list of all 91 cells (used for the board size).
from hexgrid import CELLS


# Returns the other side: BLACK becomes WHITE and WHITE becomes BLACK.
# Used whenever the turn changes. It also checks its input: anything that
# is not a player causes an error.
def opponent(player: int) -> int:
    """Return the other side."""
    # EMPTY (0) or any other number is not a player.
    if player not in (BLACK, WHITE):
        raise ValueError("Invalid player")
    # Swap the colour.
    return WHITE if player == BLACK else BLACK


# One moment of the game.
# The game screen creates one per match; the AI copies it many times.
class GameState:
    """Mutable ownership; immutable board is shared between independent copies.

    Moves use zero-based reading-order indices. Turns do not auto-pass: callers
    must call pass_turn when needed, so Minimax can count a pass as one ply.
    """

    # Creates a game state.
    # With owners=None you get the normal starting position. Passing an
    # owners list creates any position you like (the tests use this).
    # By default Black (the human) moves first.
    def __init__(self, board: Board, owners: list[int] | None = None,
                 turn: int = PLAYER_COLOR) -> None:
        # Check that turn is BLACK or WHITE (opponent() raises otherwise).
        opponent(turn)
        # The read-only board: modifiers and point values.
        self.board = board
        # For every cell: EMPTY, BLACK or WHITE. We make our own copy of the
        # list so that changing it never changes the caller's list.
        self.owners = [EMPTY] * len(CELLS) if owners is None else owners.copy()
        # For the normal start, place the six starting discs.
        if owners is None:
            # For each colour and its list of start cells...
            for player, numbers in ((BLACK, BLACK_START_NUMBERS), (WHITE, WHITE_START_NUMBERS)):
                # ...put that colour's disc on each cell (number - 1 = index).
                for n in numbers:
                    self.owners[n - 1] = player
        # Reject an owners list with the wrong length or a wrong value.
        if len(self.owners) != len(CELLS) or any(p not in (EMPTY, BLACK, WHITE) for p in self.owners):
            raise ValueError("Invalid ownership list")
        # Reject a disc sitting on a hole.
        if any(self.owners[i] != EMPTY for i in HOLES):
            raise ValueError("Holes cannot hold discs")
        # Whose move it is.
        self.turn = turn
        # The index of the latest move (drawn with a gold outline). None yet.
        self.last_move: int | None = None
        # scores[BLACK] and scores[WHITE]. Position 0 (EMPTY) is not used.
        self.scores = [0, self.recompute_score(BLACK), self.recompute_score(WHITE)]

    # Makes an independent copy of this game state.
    # Used by the game screen (to give the AI its own copy) and by the AI
    # (once for every move it tries). It must be fast, because Minimax
    # can call it many thousands of times per decision.
    def copy(self) -> "GameState":
        """Copy only mutable fields; no RNG or full score recalculation."""
        # Create an empty GameState WITHOUT running __init__. This skips
        # the checks in __init__, which would be slow and are not needed.
        clone = object.__new__(GameState)
        # The board is read-only, so the copy can share it.
        clone.board, clone.turn, clone.last_move = self.board, self.turn, self.last_move
        # The lists DO change during play, so the copy gets new lists.
        clone.owners, clone.scores = self.owners.copy(), self.scores.copy()
        return clone

    # Returns the opponent discs a move would capture (see the capture
    # example at the top of this file). An empty result means the move is
    # illegal. It only looks; it never changes the board.
    # Called by legal_moves() and by apply_move().
    def flips(self, move: int, player: int | None = None) -> tuple[int, ...]:
        """Collect all bracketed opponent discs before changing any ownership."""
        # If no player is given, use the side whose turn it is.
        player = self.turn if player is None else player
        # Discs of this colour can be captured.
        other = opponent(player)
        # Off the board, a hole, or already taken: cannot be played.
        if not 0 <= move < len(CELLS) or move in HOLES or self.owners[move] != EMPTY:
            return ()
        # Every disc this move would capture.
        captured = []
        # Look along each of the 6 straight lines starting at the move.
        for ray in RAYS[move]:
            # Opponent discs seen so far on this line.
            line = []
            # Walk along the line, one cell at a time.
            for j in ray:
                owner = self.owners[j]
                # An opponent disc: it may be captured, so remember it.
                if owner == other:
                    line.append(j)
                # Our own disc or an empty cell ends the line.
                else:
                    # Our disc after at least one opponent disc: they are
                    # trapped, so all of them are captured.
                    if owner == player and line:
                        captured.extend(line)
                    # Stop walking in this direction.
                    break
        return tuple(captured)

    # Returns every legal move as a dictionary {move index: captured discs}.
    # An empty dictionary means this side must pass.
    # Called by the game screen (to mark legal tiles), by pass_turn(),
    # is_game_over(), and by the AI for every position it examines.
    def legal_moves(self, player: int | None = None) -> dict[int, tuple[int, ...]]:
        """Map legal move indices to their complete flip sets."""
        moves = {}
        # Check every cell that is not a hole...
        for move in PLAYABLE:
            # ...and is still empty.
            if self.owners[move] == EMPTY:
                # Which discs would this move capture?
                captured = self.flips(move, player)
                # At least one capture means the move is legal.
                if captured:
                    moves[move] = captured
        return moves

    # Plays a move. This is the safe version: it checks the move first.
    # Called by the game screen for your moves and for the AI's chosen move.
    def apply_move(self, move: int) -> tuple[int, ...]:
        """Validate and commit one move, then give the turn to the other side."""
        # Work out the captures for the side whose turn it is.
        captured = self.flips(move)
        # No captures means the move is illegal.
        if not captured:
            raise ValueError("Illegal move")
        # Really change the board.
        self._apply_legal(move, captured)
        # Tell the caller which discs were captured.
        return captured

    # Plays a move WITHOUT checking it. The leading "_" means "for use inside
    # this project only". The AI uses it directly because it already got
    # the captures from legal_moves(), so checking again would waste time.
    def _apply_legal(self, move: int, captured: tuple[int, ...]) -> None:
        """Internal search fast path; captured must come from this state's legal_moves."""
        # The side moving, and the other side.
        player, other = self.turn, opponent(self.turn)
        # Place the new disc.
        self.owners[move] = player
        # Total point value of all the captured tiles.
        transferred = sum(self.board.values[i] for i in captured)
        # Turn every captured disc into the mover's colour.
        for i in captured:
            self.owners[i] = player
        # The mover gains the new tile's points plus the captured points.
        self.scores[player] += self.board.values[move] + transferred
        # The other side loses the captured points.
        # Updating the scores like this is much faster than recounting.
        self.scores[other] -= transferred
        # Give the turn to the other side, and remember this move.
        self.turn, self.last_move = other, move

    # Skips the turn of a side that has no legal move.
    # Called by the game screen's settle_turn().
    def pass_turn(self) -> None:
        """Skip only a side with no move, and never pass a terminal position."""
        # Passing is a mistake if this side CAN move, or if NEITHER side can
        # (then the game is over, not a pass).
        if self.legal_moves() or not self.legal_moves(opponent(self.turn)):
            raise ValueError("A pass is not allowed in this position")
        # Give the turn to the other side.
        self.turn = opponent(self.turn)

    # Skips the turn because your time ran out. Unlike pass_turn(), this is
    # allowed even when you have legal moves.
    # Called by the game screen's update().
    def forfeit_turn(self) -> None:
        """Timeout skips one turn without touching discs, scores, or pass counters."""
        # Just give the turn to the other side.
        self.turn = opponent(self.turn)

    # True when NEITHER side has a legal move.
    # Called by the game screen's settle_turn() and by winner().
    def is_game_over(self) -> bool:
        """No move for either side, regardless of whether empty tiles remain."""
        return not self.legal_moves() and not self.legal_moves(opponent(self.turn))

    # Returns a player's current points.
    # Called by the side panel and by the AI.
    def score(self, player: int) -> int:
        """Current sum of the fixed values of all owned tiles."""
        # _apply_legal() keeps this up to date, so no counting is needed.
        return self.scores[player]

    # Counts a player's points from scratch, by adding up every tile they own.
    # Used by __init__ for the starting scores. The tests use it to check
    # that the fast score updates in _apply_legal() are always correct.
    def recompute_score(self, player: int) -> int:
        """Reference full recomputation used to verify incremental updates."""
        return sum(self.board.values[i] for i in PLAYABLE if self.owners[i] == player)

    # How many discs a player has. Shown in the side panel only;
    # the winner is decided by points, not discs.
    def disc_count(self, player: int) -> int:
        """Secondary information only; never used to decide the winner."""
        return self.owners.count(player)

    # Returns BLACK or WHITE for the winner, or None for a draw.
    # Called by the game screen for the game-over box.
    def winner(self) -> int | None:
        """Return the winning color or None for a draw; only valid at game over."""
        # Asking before the game has ended is a mistake.
        if not self.is_game_over():
            raise ValueError("Game has not ended")
        # Equal points is a draw.
        if self.scores[BLACK] == self.scores[WHITE]:
            return None
        # Otherwise the side with more points wins.
        return BLACK if self.scores[BLACK] > self.scores[WHITE] else WHITE


# A self-check run once by main() before the window opens. It makes sure
# the board data in config.py is correct, so a typo there is found at once.
# "assert condition" stops the program with an error if the condition is
# False.
def assert_opening() -> None:
    """Startup invariant for the supplied six-disc position."""
    # Any seed works here: modifiers do not change which moves are legal.
    state = GameState(create_board(0))
    # The board must have 91 cells: 72 playable and 19 holes.
    assert len(CELLS) == 91 and len(PLAYABLE) == 72 and len(HOLES) == 19
    # For both colours...
    for player in (BLACK, WHITE):
        moves = state.legal_moves(player)
        # ...the first moves must be exactly cells 26, 34, 37, 55, 58, 66...
        assert sorted(i + 1 for i in moves) == list(OPENING_MOVE_NUMBERS)
        # ...and each of them must capture exactly one disc.
        assert all(len(flips) == 1 for flips in moves.values())
