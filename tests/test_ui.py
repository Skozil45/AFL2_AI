"""Pygame event-level integration checks under SDL's dummy video driver."""

from time import perf_counter, sleep
import pygame
import pytest
import config
from ai import AIStats
from boardgen import create_board
from engine import GameState
from ui.setup_screen import SetupScreen, Settings
from ui.game_screen import GameScreen
from test_engine import forced_pass, position


@pytest.fixture
def surface() -> pygame.Surface:
    pygame.init()
    display = pygame.display.set_mode(config.WINDOW_SIZE)
    yield display
    pygame.quit()


def click(point: tuple[int, int]) -> pygame.event.Event:
    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=point)


def key(code: int, unicode: str = "", mod: int = 0) -> pygame.event.Event:
    return pygame.event.Event(pygame.KEYDOWN, key=code, unicode=unicode, mod=mod)


def test_setup_controls_seed_validation_and_start(surface: pygame.Surface) -> None:
    setup = SetupScreen()
    assert len(setup.targets()) == 4
    setup.handle_event(click(setup.algorithm_buttons[1].rect.center))
    assert setup.algorithm == "minimax" and len(setup.targets()) == 8
    for depth, button in enumerate(setup.depth_buttons, 1):
        setup.handle_event(click(button.rect.center))
        assert setup.depth == depth
    setup.handle_event(click(setup.seed_rect.center))
    for character in "oops":
        setup.handle_event(key(ord(character), character))
    assert setup.handle_event(click(setup.start_button.rect.center)) is None and setup.error
    setup.handle_event(click(setup.seed_rect.center))
    setup.handle_event(key(pygame.K_a, mod=pygame.KMOD_CTRL))
    for character in "-123":
        setup.handle_event(key(ord(character), character))
    assert setup.handle_event(key(pygame.K_RETURN)) == Settings("minimax", 4, -123)
    setup.seed_text = ""
    assert isinstance(setup.start().seed, int)
    setup.handle_event(click(setup.algorithm_buttons[0].rect.center))
    setup.draw(surface)
    assert all(not button.enabled for button in setup.depth_buttons)
    setup.focus = 0
    setup.handle_event(key(pygame.K_TAB, mod=pygame.KMOD_SHIFT))
    assert setup.targets()[setup.focus] is setup.start_button
    assert setup.handle_event(key(pygame.K_SPACE)).algorithm == "greedy"


def test_human_clicks_numbers_restart_and_setup(surface: pygame.Surface) -> None:
    game = GameScreen(Settings("greedy", 2, 9))
    original = game.state.copy()
    game.handle_event(click(tuple(map(round, game.renderer.centers[45]))))
    assert game.state.owners == original.owners and game.banner
    game.handle_event(key(pygame.K_n))
    assert game.show_numbers
    game.handle_event(key(pygame.K_n))
    assert not game.show_numbers
    move = next(iter(game.legal))
    game.handle_event(click(tuple(map(round, game.renderer.centers[move]))))
    assert game.state.last_move == move and game.state.turn == config.WHITE
    owners = game.state.owners.copy()
    game.handle_event(click(tuple(map(round, game.renderer.centers[57]))))
    assert game.state.owners == owners
    game.handle_event(click(game.restart_button.rect.center))
    assert game.state.owners == original.owners and game.state.board == original.board
    assert game.state.turn == config.BLACK
    game.draw(surface)
    assert game.handle_event(click(game.setup_button.rect.center)) == "setup"


def test_timeout_forfeits_without_changes_and_none_disables(surface: pygame.Surface, monkeypatch: pytest.MonkeyPatch) -> None:
    game = GameScreen(Settings("greedy", 2, 1))
    owners, scores = game.state.owners.copy(), game.state.scores.copy()
    game.update(game.turn_started + 30)
    assert game.state.turn == config.WHITE
    assert game.state.owners == owners and game.state.scores == scores
    assert game.banner == config.STRINGS["timeout"]
    game.restart()
    monkeypatch.setattr(config, "TURN_TIME_LIMIT_SECONDS", None)
    game.update(game.turn_started + 10000)
    assert game.state.turn == config.BLACK
    game.draw(surface)
    game.close()


def test_ai_delay_real_worker_and_stale_result(surface: pygame.Surface) -> None:
    game = GameScreen(Settings("minimax", 4, 1))
    game.activate(next(iter(game.legal)), perf_counter())
    old_generation = game.generation
    game.launch_ai()
    deadline = perf_counter() + 5
    while game.results.empty() and perf_counter() < deadline:
        sleep(0.005)
    assert not game.results.empty()
    # A completed search is not applied until the minimum visible delay expires.
    game.update(game.turn_started + 0.1)
    assert game.pending is not None and game.state.turn == config.WHITE
    game.draw(surface)
    game.update(game.turn_started + 0.41)
    assert game.stats is not None and game.state.turn == config.BLACK
    game.restart()
    game.activate(next(iter(game.legal)), perf_counter())
    game.working = True
    invalid = AIStats(46, 0, 1, 1, 0)
    game.results.put((old_generation, (45, invalid)))
    owners = game.state.owners.copy()
    game.update(game.turn_started + 1)
    assert game.pending is None and game.state.owners == owners and not game.error
    game.results.put((game.generation, RuntimeError("test failure")))
    game.update(game.turn_started + 1)
    assert "test failure" in game.error
    game.draw(surface)
    game.close()


def test_pass_game_over_overlay_and_stopped_clocks(surface: pygame.Surface) -> None:
    game = GameScreen(Settings("greedy", 2, 1))
    game.state = forced_pass()
    game.settle_turn(perf_counter())
    assert game.state.turn == config.BLACK and "skipped" in game.banner
    game.activate(0, perf_counter())
    assert game.finished is not None
    stopped = game.finished
    game.update(stopped + 999)
    assert game.finished == stopped
    game.draw(surface)
    assert game.targets() == [game.again_button, game.overlay_setup]
    game.handle_event(click(game.again_button.rect.center))
    assert game.finished is None and game.state.board == create_board(1)
    game.state = position()
    game.settle_turn(perf_counter())
    game.draw(surface)
    assert game.handle_event(click(game.overlay_setup.rect.center)) == "setup"


def test_keyboard_board_play(surface: pygame.Surface) -> None:
    game = GameScreen(Settings("greedy", 2, 1))
    game.handle_event(key(pygame.K_TAB))
    move = game.targets()[game.focus]
    game.handle_event(key(pygame.K_RETURN))
    assert game.state.last_move == move
    game.close()


def test_timeout_followed_by_ai_pass_reports_both(surface: pygame.Surface) -> None:
    game = GameScreen(Settings("greedy", 2, 1))
    game.state = forced_pass()
    game.state.turn = config.BLACK
    game.legal = game.state.legal_moves()
    now = game.turn_started + 30
    game.update(now)
    assert game.state.turn == config.BLACK and game.turn_started == now
    assert config.STRINGS["timeout"] in game.banner
    assert "AI has no legal moves" in game.banner
    assert game.finished is None
    game.draw(surface)
    game.close()
    game = GameScreen(Settings("greedy", 2, 1))
    game.state = forced_pass()
    game.turn_started = 0
    game.settle_turn(100)
    assert game.turn_started == 100 and game.state.turn == config.BLACK
    game.close()
