"""Exact geometry, hole layout, deterministic modifiers and pixel mapping."""

import pytest
from boardgen import HOLES, PLAYABLE, create_board
from config import DIRECTIONS, HOLE_NUMBERS
from hexgrid import (CELLS, INDEX, NEIGHBORS, ROW_STARTS, axial_to_pixel,
                     cell_number, cell_from_number, distance, neighbors, pixel_to_axial)
from modifiers import OPERATORS, tile_value

EXPECTED_HOLES = {8, 10, 12, 23, 25, 27, 29, 42, 44, 46, 48, 50, 63, 65, 67, 69, 80, 82, 84}


def test_geometry_and_numbering() -> None:
    assert len(CELLS) == 91
    assert DIRECTIONS == ((1, 0), (0, 1), (-1, 1), (-1, 0), (0, -1), (1, -1))
    assert list(ROW_STARTS.values()) == [1, 7, 14, 22, 31, 41, 52, 62, 71, 79, 86]
    for n, (q, r) in enumerate(CELLS, 1):
        assert -5 <= q <= 5 and -5 <= r <= 5 and -5 <= q + r <= 5
        assert distance((q, r)) <= 5
        assert cell_number(q, r) == n
        assert cell_from_number(n) == (q, r)
        assert pixel_to_axial(*axial_to_pixel(q, r, 35, (400, 300)), 35, (400, 300)) == (q, r)
        if distance((q, r)) < 5:
            assert len(neighbors(q, r)) == 6
            assert all(i >= 0 for i in NEIGHBORS[n - 1])
    assert {n: cell_from_number(n) for n in (1, 35, 46, 84, 91)} == {
        1: (0, -5), 35: (0, -1), 46: (0, 0), 84: (0, 4), 91: (0, 5)}


@pytest.mark.parametrize("number", [0, -1, 92])
def test_reject_invalid_number(number: int) -> None:
    with pytest.raises(ValueError):
        cell_from_number(number)


def test_fixed_holes_and_connectivity() -> None:
    assert set(HOLE_NUMBERS) == EXPECTED_HOLES
    assert len(HOLES) == 19 and len(PLAYABLE) == 72
    assert INDEX[(0, 0)] in HOLES
    assert {INDEX[(-CELLS[i][0], -CELLS[i][1])] for i in HOLES} == HOLES
    for seed in (-90, 0, 1, 777, 1000000):
        assert {i for i, modifier in enumerate(create_board(seed).modifiers) if modifier is None} == HOLES
    seen, frontier = {PLAYABLE[0]}, [PLAYABLE[0]]
    while frontier:
        for j in NEIGHBORS[frontier.pop()]:
            if j in PLAYABLE and j not in seen:
                seen.add(j)
                frontier.append(j)
    assert seen == set(PLAYABLE)


def test_modifiers() -> None:
    board = create_board(123)
    assert board == create_board(123)
    assert board.modifiers != create_board(124).modifiers
    assert set(OPERATORS) == {"+", "-"}
    assert {board.modifiers[i][0] for i in PLAYABLE} == {"+", "-"}
    for i, modifier in enumerate(board.modifiers):
        if i in HOLES:
            assert modifier is None
        else:
            sign, n = modifier
            assert 1 <= n <= 5
            assert board.values[i] == 1 + n if sign == "+" else board.values[i] == 1 - n


@pytest.mark.parametrize("modifier,value", [(('+', 3), 4), (('-', 2), -1), (('-', 1), 0), (('+', 5), 6), (('-', 5), -4)])
def test_value_examples(modifier: tuple[str, int], value: int) -> None:
    assert tile_value(modifier) == value


@pytest.mark.parametrize("modifier", [("*", 2), ("+", 0), ("-", 6), ("+", 1.5)])
def test_bad_modifiers(modifier: tuple[str, int]) -> None:
    with pytest.raises(ValueError):
        tile_value(modifier)
