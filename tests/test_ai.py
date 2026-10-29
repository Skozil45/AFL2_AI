"""Crafted strategic examples and full-game legality fuzzing."""

from dataclasses import replace
from random import Random
from threading import Event
import pytest
from ai import GreedyAI, MinimaxAI, SearchCancelled
from boardgen import PLAYABLE, create_board
from config import BLACK, WHITE
from engine import GameState, opponent
from test_engine import position, forced_pass


def reference(state: GameState, depth: int, color: int) -> tuple[int, int]:
    """Independent exhaustive oracle; count every descendant including passes."""
    if depth == 0 or state.is_game_over():
        return state.recompute_score(color) - state.recompute_score(opponent(color)), 1
    moves = state.legal_moves()
    if not moves:
        child = state.copy()
        child.pass_turn()
        value, count = reference(child, depth - 1, color)
        return value, count + 1
    results = []
    for move in moves:
        child = state.copy()
        child.apply_move(move)
        results.append(reference(child, depth - 1, color))
    values = [v for v, _ in results]
    return (max(values) if state.turn == color else min(values)), 1 + sum(n for _, n in results)


def test_greedy_values_points_over_flip_count() -> None:
    state = position((34, 35, 36, 45, 57), (47, 56), WHITE)
    legal = state.legal_moves()
    move, stats = GreedyAI(seed=0).choose_move(state)
    scores = {}
    for candidate in legal:
        child = state.copy()
        child.apply_move(candidate)
        scores[candidate] = child.score(WHITE)
    assert move == 65 and stats.evaluation == max(scores.values())
    assert len(legal[move]) == 1 < max(map(len, legal.values()))
    assert stats.nodes == stats.candidates == len(legal)


def test_depth_two_avoids_a_depth_one_trap() -> None:
    # Fixed seed-1 position: #58 looks best immediately; #64/#66 survive the reply better.
    state = position((35, 36, 37, 45, 47, 55, 56, 57), (24, 26, 34), WHITE)
    one, _ = MinimaxAI(1, seed=0).choose_move(state)
    two, stats = MinimaxAI(2, seed=0).choose_move(state)
    assert one == 57 and two in (63, 65)
    values = {}
    for move in state.legal_moves():
        child = state.copy()
        child.apply_move(move)
        values[move] = reference(child, 1, WHITE)[0]
    assert values[two] == stats.evaluation == -5 > values[one] == -9


@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_minimax_matches_exhaustive_oracle(depth: int) -> None:
    state = GameState(create_board(2), turn=WHITE)
    owners, scores = state.owners.copy(), state.scores.copy()
    move, stats = MinimaxAI(depth, seed=12).choose_move(state)
    values, count = {}, 0
    for candidate in state.legal_moves():
        child = state.copy()
        child.apply_move(candidate)
        value, nodes = reference(child, depth - 1, WHITE)
        values[candidate] = value
        count += nodes
    assert move in state.legal_moves() and values[move] == max(values.values()) == stats.evaluation
    assert stats.nodes == count and stats.chosen_tile == move + 1 and stats.time_ms >= 0
    assert state.owners == owners and state.scores == scores and state.turn == WHITE


@pytest.mark.parametrize("algorithm", [GreedyAI, MinimaxAI])
def test_ties_are_random_and_reproducible(algorithm: type) -> None:
    board = create_board(1)
    # All playable tiles have the legal modifier +1, hence identical values.
    board = replace(board, modifiers=tuple(("+", 1) if i in PLAYABLE else None for i in range(91)),
                    values=tuple(2 if i in PLAYABLE else 0 for i in range(91)))
    state = GameState(board, turn=WHITE)
    def choices(seed: int) -> list[int]:
        ai = algorithm(seed=seed)
        return [ai.choose_move(state)[0] for _ in range(25)]
    selected = choices(5)
    assert selected == choices(5)
    assert len(set(selected)) > 1 and set(selected) <= state.legal_moves().keys()


def test_pass_consumes_one_search_level() -> None:
    state = forced_pass()
    ai = MinimaxAI(2)
    for depth in (1, 2, 3):
        ai.nodes = 0
        value = ai._search(state.copy(), depth)
        expected, nodes = reference(state, depth, WHITE)
        assert value == expected and ai.nodes == nodes
    ai.nodes = 0
    assert ai._search(state, 1) == state.score(WHITE) - state.score(BLACK)
    assert ai.nodes == 2


@pytest.mark.parametrize("algorithm", [GreedyAI, MinimaxAI])
def test_ai_validation_and_cancellation(algorithm: type) -> None:
    state = GameState(create_board(0))
    with pytest.raises(ValueError):
        algorithm().choose_move(state)
    with pytest.raises(ValueError):
        MinimaxAI(5)
    cancel = Event()
    cancel.set()
    state.turn = WHITE
    with pytest.raises(SearchCancelled):
        algorithm(cancel=cancel).choose_move(state)
    with pytest.raises(ValueError):
        algorithm().choose_move(forced_pass())


@pytest.mark.parametrize("algorithm", [GreedyAI, MinimaxAI])
def test_decision_stats_reset_between_calls(algorithm: type) -> None:
    state = GameState(create_board(1), turn=WHITE)
    ai = algorithm(seed=0)
    _, first = ai.choose_move(state)
    _, second = ai.choose_move(state)
    assert first.nodes == second.nodes > 0
    assert first.candidates == second.candidates == len(state.legal_moves())
    assert first.evaluation == second.evaluation


@pytest.mark.parametrize("seed", range(40))
def test_full_game_fuzz(seed: int) -> None:
    state, rng = GameState(create_board(seed)), Random(seed)
    agents = {BLACK: GreedyAI(BLACK, seed), WHITE: MinimaxAI(1 + seed % 2, WHITE, seed + 1)}
    turns = 0
    while not state.is_game_over():
        legal = state.legal_moves()
        if not legal:
            state.pass_turn()
            continue
        before = state.owners.copy(), state.scores.copy(), state.turn
        move, _ = agents[state.turn].choose_move(state)
        assert move in legal
        assert (state.owners, state.scores, state.turn) == before
        # Mix random play and both algorithms to explore different reachable states.
        state.apply_move(rng.choice(list(legal)) if turns % 3 == 0 else move)
        assert all(state.score(p) == state.recompute_score(p) for p in (BLACK, WHITE))
        turns += 1
        assert turns <= 66
