"""Rules, all six directions, passes, forfeits and score conservation."""

from random import Random
import pytest
from boardgen import HOLES, PLAYABLE, RAYS, create_board
from config import (BLACK, WHITE, EMPTY, PLAYER_COLOR, TURN_TIME_LIMIT_SECONDS,
                    WHITE_START_NUMBERS, BLACK_START_NUMBERS, OPENING_MOVE_NUMBERS)
from engine import GameState, assert_opening
from hexgrid import CELLS, NEIGHBORS


def position(black: tuple[int, ...] = (), white: tuple[int, ...] = (),
             turn: int = BLACK, seed: int = 1) -> GameState:
    """Construct a test position from 1-based reading-order numbers."""
    owners = [EMPTY] * len(CELLS)
    for player, numbers in ((BLACK, black), (WHITE, white)):
        for n in numbers:
            owners[n - 1] = player
    return GameState(create_board(seed), owners, turn)


def forced_pass() -> GameState:
    """Only #1 is empty; Black can bracket White #2 against Black #3."""
    owners = [EMPTY if i in HOLES or i == 0 else BLACK for i in range(len(CELLS))]
    owners[1] = WHITE
    return GameState(create_board(1), owners, WHITE)


def test_opening_and_config() -> None:
    assert_opening()
    state = GameState(create_board(2))
    assert TURN_TIME_LIMIT_SECONDS == 30 and PLAYER_COLOR == BLACK and state.turn == BLACK
    assert tuple(i + 1 for i, p in enumerate(state.owners) if p == WHITE) == WHITE_START_NUMBERS
    assert tuple(i + 1 for i, p in enumerate(state.owners) if p == BLACK) == BLACK_START_NUMBERS
    for player in (BLACK, WHITE):
        moves = state.legal_moves(player)
        assert tuple(m + 1 for m in moves) == OPENING_MOVE_NUMBERS
        assert all(len(captured) == 1 for captured in moves.values())


@pytest.mark.parametrize("direction", range(6), ids=["east", "southeast", "southwest", "west", "northwest", "northeast"])
def test_flipping_each_direction(direction: int) -> None:
    move = next(i for i in PLAYABLE if len(RAYS[i][direction]) >= 3)
    ray = RAYS[move][direction]
    state = position((ray[2] + 1,), (ray[0] + 1, ray[1] + 1))
    assert state.flips(move) == (ray[0], ray[1])
    assert state.apply_move(move) == (ray[0], ray[1])
    assert all(state.owners[i] == BLACK for i in (move, *ray[:3]))
    assert state.score(BLACK) == state.recompute_score(BLACK)
    assert state.score(WHITE) == 0


def test_multi_direction_flip() -> None:
    move = next(i for i in PLAYABLE if sum(len(ray) >= 2 for ray in RAYS[i]) >= 3)
    rays = [ray for ray in RAYS[move] if len(ray) >= 2]
    state = position(tuple(ray[1] + 1 for ray in rays), tuple(ray[0] + 1 for ray in rays))
    assert set(state.flips(move)) == {ray[0] for ray in rays}
    state.apply_move(move)
    assert all(state.owners[ray[0]] == BLACK for ray in rays)


def test_illegal_occupied_hole_empty_and_no_flank() -> None:
    state = GameState(create_board(1))
    for move in (34, 45, 0, -1, 91):
        assert not state.flips(move)
        with pytest.raises(ValueError):
            state.apply_move(move)
    # Empty #3 breaks a potential row beginning at #1 -> White #2.
    state = position((), (2,))
    assert not state.flips(0)


def test_hole_breaks_line() -> None:
    # #7 -> hole #8 -> #9 is not traversable, even with discs beyond it.
    state = position((11,), (9,))
    assert not state.flips(6)
    # This parity layout places holes either immediately next to a playable
    # origin or outside its line entirely; no playable-opponent-hole triple exists.
    for move in PLAYABLE:
        for direction, ray in enumerate(RAYS[move]):
            assert all(i not in HOLES for i in ray)
            if NEIGHBORS[move][direction] in HOLES:
                assert ray == ()


def test_edge_breaks_line_no_wrap() -> None:
    move, direction = next((i, d) for i in PLAYABLE for d, ray in enumerate(RAYS[i])
                           if ray and NEIGHBORS[ray[-1]][d] == -1)
    state = position((), tuple(i + 1 for i in RAYS[move][direction]))
    assert not state.flips(move)


def test_pass_terminal_and_full_board() -> None:
    state = forced_pass()
    assert not state.legal_moves() and not state.is_game_over()
    owners, scores = state.owners.copy(), state.scores.copy()
    state.pass_turn()
    assert state.turn == BLACK and state.owners == owners and state.scores == scores
    assert set(state.legal_moves()) == {0}
    state.apply_move(0)
    assert state.is_game_over() and state.disc_count(BLACK) == 72
    assert state.winner() == BLACK
    empty = position()
    assert empty.is_game_over() and empty.winner() is None
    with pytest.raises(ValueError):
        empty.pass_turn()
    with pytest.raises(ValueError):
        GameState(create_board(1)).pass_turn()


def test_forfeit_is_not_a_pass_or_terminal_counter() -> None:
    state = GameState(create_board(1))
    owners, scores = state.owners.copy(), state.scores.copy()
    for expected in (WHITE, BLACK, WHITE, BLACK):
        state.forfeit_turn()
        assert state.turn == expected
        assert state.owners == owners and state.scores == scores
        assert not state.is_game_over()


def test_scores_independent_of_move_order() -> None:
    first = position((3, 90), (2, 89), BLACK)
    second = position((3, 90), (2, 89), WHITE)
    for state, moves in ((first, (0, 90)), (second, (90, 0))):
        for move in moves:
            state.apply_move(move)
            for color in (BLACK, WHITE):
                assert state.score(color) == state.recompute_score(color)
    assert first.owners == second.owners and first.scores == second.scores


def test_negative_scores_winner_and_draw() -> None:
    board = create_board(1)
    negative = next(i for i in PLAYABLE if board.values[i] < 0)
    state = position((negative + 1,))
    assert state.score(BLACK) < 0 and state.winner() == WHITE
    assert position().winner() is None
    zero = next(i for i in PLAYABLE if board.values[i] == 0)
    assert position((zero + 1,)).winner() is None
    assert position((), (negative + 1,)).winner() == BLACK


def test_incremental_equals_recomputed_every_turn() -> None:
    for seed in range(20):
        state, rng = GameState(create_board(seed)), Random(seed)
        while not state.is_game_over():
            moves = state.legal_moves()
            if not moves:
                state.pass_turn()
            else:
                state.apply_move(rng.choice(list(moves)))
            assert all(state.score(color) == state.recompute_score(color) for color in (BLACK, WHITE))
            assert all(state.owners[i] == EMPTY for i in HOLES)


def test_copy_is_independent_and_rejects_hole_ownership() -> None:
    state = GameState(create_board(1))
    clone = state.copy()
    clone.apply_move(next(iter(clone.legal_moves())))
    assert clone.board is state.board and clone.owners != state.owners
    assert state.last_move is None
    with pytest.raises(ValueError):
        position((46,))
