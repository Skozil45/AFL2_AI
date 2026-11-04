"""Live match controller, human timer and isolated background AI worker."""

from queue import Queue, Empty
from threading import Thread, Event
from time import perf_counter
import pygame
import config
from ai import GreedyAI, MinimaxAI, AIStats, SearchCancelled
from boardgen import create_board
from engine import GameState
from ui import gfx
from ui.renderer import BoardRenderer, disc
from ui.setup_screen import Settings
from ui.widgets import Button, text, tr, wrapped_text, tab_index

PANEL_X, PANEL_WIDTH = 916, 352
PANEL_LEFT, PANEL_RIGHT = PANEL_X + 16, PANEL_X + PANEL_WIDTH - 16
PANEL_INNER = PANEL_RIGHT - PANEL_LEFT


def card(surface: pygame.Surface, y: int, height: int) -> None:
    """One section of the side panel."""
    gfx.rect(surface, config.COLORS["panel"], (PANEL_X, y, PANEL_WIDTH, height), border_radius=8)


def row(surface: pygame.Surface, label: str, value: str, y: int, color: str = "text") -> None:
    """A label on the left with its value lined up on the right."""
    text(surface, label, (PANEL_LEFT, y), config.FONT_SMALL, "muted")
    text(surface, value, (PANEL_RIGHT, y), config.FONT_SMALL, color, max_width=PANEL_INNER // 2, right=True)


class GameScreen:
    """All Pygame operations stay on the main thread."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.renderer = BoardRenderer(pygame.Rect(20, 63, 880, 650))
        self.restart_button = Button(pygame.Rect(916, 734, 170, 48), tr("restart"))
        self.setup_button = Button(pygame.Rect(1098, 734, 170, 48), tr("new_setup"))
        self.again_button = Button(pygame.Rect(404, 476, 220, 48), tr("again"))
        self.overlay_setup = Button(pygame.Rect(644, 476, 230, 48), tr("new_setup"))
        self.results: Queue[tuple[int, tuple[int, AIStats] | Exception]] = Queue()
        self.generation = 0
        self.cancel = Event()
        self.restart()

    def restart(self) -> None:
        """Recreate the same modifiers and invalidate any earlier worker result."""
        self.cancel.set()
        self.cancel = Event()
        self.generation += 1
        self.state = GameState(create_board(self.settings.seed))
        self.started = self.turn_started = perf_counter()
        self.finished: float | None = None
        self.working = False
        self.pending: tuple[int, AIStats] | None = None
        self.stats: AIStats | None = None
        self.banner, self.banner_until, self.error = "", 0.0, ""
        self.show_numbers, self.focus = False, -1
        # ASSUMPTION: UI tie-breaking is unseeded; the board seed affects modifiers only.
        self.ai = (GreedyAI(cancel=self.cancel) if self.settings.algorithm == "greedy" else
                   MinimaxAI(self.settings.depth, cancel=self.cancel))
        self.legal = self.state.legal_moves()

    def close(self) -> None:
        """Cancel work without blocking the window when leaving a match."""
        self.cancel.set()
        self.generation += 1

    def say(self, message: str, now: float) -> None:
        """Retain transient feedback long enough to read."""
        self.banner, self.banner_until = message, now + config.BANNER_SECONDS

    def settle_turn(self, now: float) -> None:
        """Resolve a genuine no-move pass or stop clocks at game over."""
        self.legal = self.state.legal_moves()
        if not self.legal:
            if self.state.is_game_over():
                self.finished = now
                self.focus = 0
                return
            name = tr("player_short" if self.state.turn == config.PLAYER_COLOR else "ai_short")
            self.state.pass_turn()
            self.say(tr("pass", name=name), now)
            self.legal = self.state.legal_moves()
        self.turn_started = now
        self.focus = -1

    def launch_ai(self) -> None:
        """Snapshot on the main thread; worker never reads the live state."""
        self.working = True
        generation, snapshot, ai, queue = self.generation, self.state.copy(), self.ai, self.results

        def work() -> None:
            try:
                result = ai.choose_move(snapshot)
            except SearchCancelled:
                return
            except Exception as error:
                queue.put((generation, error))
            else:
                queue.put((generation, result))

        Thread(target=work, daemon=True, name=f"hex-reversi-ai-{generation}").start()

    def update(self, now: float | None = None) -> None:
        """Advance timers and accept only results belonging to this match."""
        now = perf_counter() if now is None else now
        if self.finished is not None or self.error:
            return
        if self.state.turn == config.PLAYER_COLOR:
            limit = config.TURN_TIME_LIMIT_SECONDS
            if limit is not None and now - self.turn_started >= limit:
                self.state.forfeit_turn()
                self.settle_turn(now)
                message = tr("timeout")
                if self.finished is None and self.state.turn == config.PLAYER_COLOR:
                    message = tr("combined_banner", first=message, second=self.banner)
                self.say(message, now)
            return
        if not self.working:
            self.launch_ai()
        while True:
            try:
                generation, result = self.results.get_nowait()
            except Empty:
                break
            if generation == self.generation:
                if isinstance(result, Exception):
                    self.error = tr("ai_error", error=str(result))
                    return
                self.pending = result
        if self.pending is not None and now - self.turn_started >= config.AI_MIN_DELAY_SECONDS:
            move, self.stats = self.pending
            if move not in self.legal:
                self.error = tr("ai_error", error=tr("illegal"))
                return
            self.state.apply_move(move)
            self.pending, self.working = None, False
            self.settle_turn(now)

    def targets(self) -> list[int | Button]:
        """Legal moves followed by match controls; overlay owns focus at the end."""
        if self.finished is not None:
            return [self.again_button, self.overlay_setup]
        return (list(self.legal) if self.state.turn == config.PLAYER_COLOR else []) + [self.restart_button, self.setup_button]

    def activate(self, target: int | Button, now: float) -> str | None:
        """Return 'setup' when the outer application should change screen."""
        if target is self.setup_button or target is self.overlay_setup:
            self.close()
            return "setup"
        if target is self.restart_button or target is self.again_button:
            self.restart()
        elif isinstance(target, int) and target in self.legal and self.state.turn == config.PLAYER_COLOR:
            self.state.apply_move(target)
            self.settle_turn(now)
        return None

    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Ignore board clicks during AI work; controls remain responsive."""
        now = perf_counter()
        human_at_receipt = self.state.turn == config.PLAYER_COLOR
        # Expire the turn before accepting a click delivered after the deadline.
        self.update(now)
        targets = self.targets()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_n:
                self.show_numbers = not self.show_numbers
            elif event.key == pygame.K_TAB:
                self.focus = tab_index(self.focus, len(targets), bool(event.mod & pygame.KMOD_SHIFT))
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and 0 <= self.focus < len(targets):
                return self.activate(targets[self.focus], now)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for target in targets:
                if isinstance(target, Button) and target.rect.collidepoint(event.pos):
                    return self.activate(target, now)
            if human_at_receipt and self.finished is None and self.state.turn == config.PLAYER_COLOR and not self.error:
                move = self.renderer.hit_test(event.pos)
                if move in self.legal:
                    return self.activate(move, now)
                if self.renderer.rect.collidepoint(event.pos):
                    self.say(tr("illegal"), now)
        return None

    def lead_text(self) -> str:
        """Describe the score gap by who is ahead, not as a signed difference."""
        lead = self.state.score(config.PLAYER_COLOR) - self.state.score(config.AI_COLOR)
        if lead == 0:
            return tr("tied")
        name = tr("player_short" if lead > 0 else "ai_short")
        return tr("won_by" if self.finished is not None else "leads_by", name=name, points=abs(lead))

    def draw_status(self, surface: pygame.Surface, human: bool) -> None:
        """Whose turn it is, or that the match has ended."""
        card(surface, 18, 54)
        title = tr("over" if self.finished is not None else "player_turn" if human else "thinking")
        text(surface, title, (PANEL_LEFT, 32), config.FONT_HEADING, max_width=PANEL_INNER - 40)
        if self.finished is None:
            disc(surface, (PANEL_RIGHT - 14, 45), 13, self.state.turn)

    def draw_scores(self, surface: pygame.Surface) -> None:
        """Both sides next to each other, with the gap between them underneath."""
        card(surface, 80, 142)
        for x, owner, name in ((PANEL_LEFT, config.PLAYER_COLOR, "player_short"),
                               (PANEL_LEFT + 168, config.AI_COLOR, "ai_short")):
            disc(surface, (x + 10, 104), 9, owner)
            text(surface, tr(name), (x + 28, 95), config.FONT_SMALL, "muted")
            text(surface, str(self.state.score(owner)), (x, 118), config.FONT_TITLE, max_width=150)
            text(surface, tr("disc_count", count=self.state.disc_count(owner)), (x, 160), config.FONT_SMALL, "muted")
        gfx.rect(surface, config.COLORS["disabled"], (PANEL_LEFT, 184, PANEL_INNER, 1))
        text(surface, self.lead_text(), (PANEL_X + PANEL_WIDTH / 2, 203), config.FONT_SMALL, "gold", True)

    def draw_clocks(self, surface: pygame.Surface, now: float, human: bool) -> None:
        """The clock that matters right now, its bar, and the total game time."""
        card(surface, 230, 86)
        limit, fill = config.TURN_TIME_LIMIT_SECONDS, 0.0
        color = "text"
        if self.finished is not None:
            text(surface, tr("timer_stopped"), (PANEL_LEFT, 242), config.FONT_SMALL, "muted")
        elif not human:
            row(surface, tr("ai_time"), tr("seconds", seconds=now - self.turn_started), 242)
        elif limit is None:
            text(surface, tr("limit_off"), (PANEL_LEFT, 242), config.FONT_SMALL, "muted")
        else:
            remaining = max(0.0, limit - (now - self.turn_started))
            fill = remaining / limit
            color = "red" if remaining <= config.TIMER_WARNING_SECONDS else "gold"
            row(surface, tr("your_time"), tr("seconds", seconds=remaining), 242, color)
        gfx.rect(surface, config.COLORS["disabled"], (PANEL_LEFT, 266, PANEL_INNER, 6))
        gfx.rect(surface, config.COLORS[color], (PANEL_LEFT, 266, PANEL_INNER * fill, 6))
        row(surface, tr("game_time"), tr("seconds", seconds=now - self.started), 284)

    def draw_decision(self, surface: pygame.Surface) -> None:
        """The numbers behind the AI's last move, one per row."""
        card(surface, 324, 178)
        text(surface, tr("ai_info"), (PANEL_LEFT, 336))
        if self.stats is None:
            text(surface, tr("no_decision"), (PANEL_LEFT, 368), config.FONT_SMALL, "muted")
            return
        rows = ((tr("chosen"), tr("chosen_value", number=self.stats.chosen_tile)),
                (tr("evaluation"), tr("evaluation_value", value=self.stats.evaluation)),
                (tr("candidates"), tr("count_value", count=self.stats.candidates)),
                (tr("nodes"), tr("count_value", count=self.stats.nodes)),
                (tr("decision_time"), tr("decision_value", ms=self.stats.time_ms)))
        for i, (label, value) in enumerate(rows):
            row(surface, label, value, 368 + i * 26)

    def draw_match(self, surface: pygame.Surface) -> None:
        """The settings of this match, which never change while it runs."""
        card(surface, 510, 126)
        text(surface, tr("match_info"), (PANEL_LEFT, 522))
        algorithm = tr(self.settings.algorithm)
        if self.settings.algorithm == "minimax":
            algorithm = tr("config", algorithm=algorithm, depth=self.settings.depth)
        row(surface, tr("ai_short"), algorithm, 554)
        row(surface, tr("seed"), str(self.settings.seed), 580)
        row(surface, tr("modifiers"), tr("modifier_range"), 606)

    def draw_message(self, surface: pygame.Surface, now: float) -> None:
        """A pass, timeout or error, outlined so it stands out from the statistics."""
        if not self.error and now >= self.banner_until:
            return
        color = "red" if self.error else "gold"
        card(surface, 644, 82)
        gfx.rect(surface, config.COLORS[color], (PANEL_X, 644, PANEL_WIDTH, 82), 2, border_radius=8)
        wrapped_text(surface, self.error or self.banner, pygame.Rect(PANEL_LEFT, 656, PANEL_INNER, 60), color)

    def draw(self, surface: pygame.Surface) -> None:
        """Render the board, scores, timer, search statistics and final overlay."""
        now = self.finished if self.finished is not None else perf_counter()
        surface.fill(config.COLORS["background"])
        text(surface, tr("title"), (35, 19), config.FONT_HEADING)
        text(surface, self.renderer.hover_text(self.state), (370, 29), config.FONT_SMALL)
        targets = self.targets()
        focused = targets[self.focus] if 0 <= self.focus < len(targets) else None
        human = self.state.turn == config.PLAYER_COLOR
        self.renderer.draw(surface, self.state, self.legal if human and self.finished is None else {},
                           self.show_numbers, focused if isinstance(focused, int) else None)
        self.renderer.legend(surface, 735)
        base = config.BASE_VALUE
        text(surface, tr("value_note", base=base, plus=base + 3, minus=base - 2), (self.renderer.rect.centerx, 777),
             config.FONT_SMALL, "muted", center=True)
        self.draw_status(surface, human)
        self.draw_scores(surface)
        self.draw_clocks(surface, now, human)
        self.draw_decision(surface)
        self.draw_match(surface)
        self.draw_message(surface, now)
        self.restart_button.draw(surface, focused is self.restart_button)
        self.setup_button.draw(surface, focused is self.setup_button)
        if self.finished is not None:
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 175))
            surface.blit(shade, (0, 0))
            gfx.rect(surface, config.COLORS["panel"], (350, 232, 580, 320), border_radius=10)
            winner = self.state.winner()
            result = tr("draw") if winner is None else tr("winner", name=tr("player_short" if winner == config.PLAYER_COLOR else "ai_short"))
            text(surface, result, (640, 279), config.FONT_TITLE, center=True)
            lines = [tr("score", name=tr("player"), score=self.state.score(config.BLACK)),
                     tr("score", name=tr("ai"), score=self.state.score(config.WHITE)),
                     self.lead_text()]
            for i, label in enumerate(lines):
                text(surface, label, (640, 345 + i * 32), center=True)
            self.again_button.draw(surface, focused is self.again_button)
            self.overlay_setup.draw(surface, focused is self.overlay_setup)
