"""Live match controller, human timer and isolated background AI worker."""

# =============================================================================
# FILE: ui/game_screen.py  -  runs one match, from the first move to game over.
#
# main.py creates GameScreen(settings) after the setup screen. Then, every
# frame, main.py calls these three methods in this order:
#   handle_event(event)  - for every mouse click or key press
#   update()             - timers, the AI's answer, playing the AI's move
#   draw(surface)        - the board, side panel, messages, game-over box
#
# YOUR TURN:
#   click a legal tile -> handle_event() -> activate() -> apply_move()
#   -> settle_turn() (does someone have to pass? is the game over?)
#   If your 30 seconds run out: update() -> forfeit_turn() -> settle_turn().
#
# AI TURN:
#   update() -> launch_ai() starts a background thread -> the thread runs
#   choose_move() and puts its answer in a queue -> a later update() takes
#   the answer out -> waits until at least 0.4 s have passed -> apply_move()
#   -> settle_turn().
#
# -----------------------------------------------------------------------------
# CONCEPT: WHY THE AI RUNS IN A "THREAD"
# -----------------------------------------------------------------------------
# The main loop must run 60 times per second to keep the window alive. If
# the AI thought inside the main loop, the window would freeze until it
# finished (Minimax at depth 4 can take seconds).
#
# A THREAD is a second worker that runs at the same time as the main loop.
# The AI thinks in its own thread while the main loop keeps drawing frames.
#
# Three tools make this safe:
#   - The AI gets a COPY of the game, so the two workers never change the
#     same data at the same time.
#   - A QUEUE is a thread-safe mailbox. The AI thread puts its answer in;
#     the main loop checks the mailbox every frame without waiting.
#   - An EVENT is a thread-safe on/off flag. When you press Restart, the
#     main loop switches it on, and the AI thread sees it and stops.
#
# -----------------------------------------------------------------------------
# CONCEPT: THE "GENERATION" NUMBER
# -----------------------------------------------------------------------------
# If you restart while the AI is thinking, an answer for the OLD game might
# still arrive in the mailbox. Each match has a generation number, which
# goes up by 1 on every restart. Every answer is labelled with the
# generation it was made for, and answers with an old number are ignored.
#
# All Pygame drawing happens in the main thread; the AI thread never draws.
# =============================================================================

# Queue: the thread-safe mailbox. Empty: the error raised when it has nothing.
from queue import Queue, Empty
# Thread: a background worker. Event: a thread-safe on/off flag.
from threading import Thread, Event
# A precise clock for the timers.
from time import perf_counter
# Rectangles, events and drawing.
import pygame
# Timings, colours, fonts and player colours.
import config
# The AI players, their statistics, and the "stop" error.
from ai import GreedyAI, MinimaxAI, AIStats, SearchCancelled
# Builds the board from the seed.
from boardgen import create_board
# The game rules.
from engine import GameState
# Draws the board.
from ui.renderer import BoardRenderer
# The choices made on the setup screen.
from ui.setup_screen import Settings
# Shared helpers: buttons, text, translations, Tab focus.
from ui.widgets import Button, text, tr, wrapped_text, tab_index


class GameScreen:
    """All Pygame operations stay on the main thread."""

    # Creates the screen. Called by main.py with the Settings from the setup screen.
    def __init__(self, settings: Settings) -> None:
        # Algorithm, depth and seed for this match.
        self.settings = settings
        # The board fills the left part of the window (x, y, width, height).
        self.renderer = BoardRenderer(pygame.Rect(20, 63, 880, 650))
        # Side panel buttons.
        self.restart_button = Button(pygame.Rect(934, 655, 147, 46), tr("restart"))
        self.setup_button = Button(pygame.Rect(1093, 655, 159, 46), tr("new_setup"))
        # Game-over box buttons.
        self.again_button = Button(pygame.Rect(404, 476, 220, 48), tr("again"))
        self.overlay_setup = Button(pygame.Rect(644, 476, 230, 48), tr("new_setup"))
        # The mailbox. Each message is (generation, answer) or (generation, error).
        self.results: Queue[tuple[int, tuple[int, AIStats] | Exception]] = Queue()
        # The match counter (see "generation" at the top of this file).
        self.generation = 0
        # A placeholder flag; restart() replaces it straight away.
        self.cancel = Event()
        # Set up the first match.
        self.restart()

    # Starts a fresh match with the SAME seed, so the board is the same.
    # Called by __init__, by the Restart button, and by Play Again.
    def restart(self) -> None:
        """Recreate the same modifiers and invalidate any earlier worker result."""
        # Tell the old match's AI thread (if any) to stop...
        self.cancel.set()
        # ...and make a new, switched-off flag for the new match.
        self.cancel = Event()
        # Answers labelled with the old generation will now be ignored.
        self.generation += 1
        # The starting position on a board built from the seed.
        self.state = GameState(create_board(self.settings.seed))
        # Start the game clock and the first turn's clock.
        self.started = self.turn_started = perf_counter()
        # The time the game ended (None while it is still being played).
        self.finished: float | None = None
        # True while an AI thread is working on this turn.
        self.working = False
        # The AI's answer, kept here until the minimum delay has passed.
        self.pending: tuple[int, AIStats] | None = None
        # The latest AI decision, shown in the side panel.
        self.stats: AIStats | None = None
        # A temporary message, the time it disappears, and an AI error ("" = none).
        self.banner, self.banner_until, self.error = "", 0.0, ""
        # Cell numbers hidden; no keyboard focus (-1).
        self.show_numbers, self.focus = False, -1
        # ASSUMPTION: UI tie-breaking is unseeded; the board seed affects modifiers only.
        # Create the AI chosen on the setup screen, giving it the new cancel flag.
        self.ai = (GreedyAI(cancel=self.cancel) if self.settings.algorithm == "greedy" else
                   MinimaxAI(self.settings.depth, cancel=self.cancel))
        # The legal moves of the side to move (you, Black, at the start).
        self.legal = self.state.legal_moves()

    # Stops the AI when leaving the match. It does not wait for the thread.
    # Called by main.py when the window closes, and by activate() for New Setup.
    def close(self) -> None:
        """Cancel work without blocking the window when leaving a match."""
        # Tell the AI thread to stop...
        self.cancel.set()
        # ...and ignore anything it still sends.
        self.generation += 1

    # Shows a temporary message (pass, timeout, illegal click) for 4 seconds.
    def say(self, message: str, now: float) -> None:
        """Retain transient feedback long enough to read."""
        self.banner, self.banner_until = message, now + config.BANNER_SECONDS

    # Decides what happens after EVERY move, timeout or pass:
    # game over, an automatic pass, or simply the next turn.
    def settle_turn(self, now: float) -> None:
        """Resolve a genuine no-move pass or stop clocks at game over."""
        # The legal moves of the side whose turn it is now.
        self.legal = self.state.legal_moves()
        # This side cannot move...
        if not self.legal:
            # ...and neither can the other: the game is over.
            if self.state.is_game_over():
                self.finished = now  # Stop the clocks.
                self.focus = 0  # Put the keyboard focus on "Play Again".
                return
            # Otherwise this side must pass. Remember its name for the message.
            name = tr("player_short" if self.state.turn == config.PLAYER_COLOR else "ai_short")
            # Skip its turn, and explain why.
            self.state.pass_turn()
            self.say(tr("pass", name=name), now)
            # The legal moves of the other side.
            self.legal = self.state.legal_moves()
        # The new turn's clock starts now.
        self.turn_started = now
        # Clear the keyboard focus.
        self.focus = -1

    # Starts the AI thinking in a background thread (see the threads concept
    # at the top of this file). Called by update() at the start of an AI turn.
    def launch_ai(self) -> None:
        """Snapshot on the main thread; worker never reads the live state."""
        # Remember that a thread is running, so update() doesn't start another.
        self.working = True
        # Collect everything the thread needs NOW: the generation number, a
        # copy of the game, the AI, and the mailbox. The thread uses only these.
        generation, snapshot, ai, queue = self.generation, self.state.copy(), self.ai, self.results

        # The job the thread runs. A function inside a function can use the
        # variables above (generation, snapshot, ai, queue).
        def work() -> None:
            # The AI may be told to stop, or may crash.
            try:
                # Think. This can take a while for Minimax at depth 4.
                result = ai.choose_move(snapshot)
            # The match was restarted or left: just drop the answer.
            except SearchCancelled:
                return
            # A real bug in the AI: send the error to the main loop to show it.
            except Exception as error:
                queue.put((generation, error))
            # "else" runs only if there was no error: send the answer.
            else:
                queue.put((generation, result))

        # Create the thread and start it. daemon=True means it will not keep
        # the program running after the window closes.
        Thread(target=work, daemon=True, name=f"hex-reversi-ai-{generation}").start()

    # Moves the game forward in time: timers, the AI's answer, and playing
    # the AI's move. Called by main.py every frame, and by handle_event()
    # before each event. Tests can pass their own "now" to control time.
    def update(self, now: float | None = None) -> None:
        """Advance timers and accept only results belonging to this match."""
        # The current time (unless a test gave one).
        now = perf_counter() if now is None else now
        # After game over or an AI error, nothing moves forward any more.
        if self.finished is not None or self.error:
            return
        # ---- YOUR TURN ----
        if self.state.turn == config.PLAYER_COLOR:
            # The time limit (30 s, or None for no limit).
            limit = config.TURN_TIME_LIMIT_SECONDS
            # Your time ran out:
            if limit is not None and now - self.turn_started >= limit:
                # Skip your turn, then check if the AI must pass or the game ended.
                self.state.forfeit_turn()
                self.settle_turn(now)
                # The "Time's up" message.
                message = tr("timeout")
                # If the AI had to pass straight back to you, show both messages.
                if self.finished is None and self.state.turn == config.PLAYER_COLOR:
                    message = tr("combined_banner", first=message, second=self.banner)
                self.say(message, now)
            # Your moves come through handle_event(), not here.
            return
        # ---- AI TURN ----
        # No thread yet for this turn: start one.
        if not self.working:
            self.launch_ai()
        # Read every message in the mailbox, without waiting.
        while True:
            try:
                generation, result = self.results.get_nowait()
            # The mailbox is empty: stop reading for this frame.
            except Empty:
                break
            # Only answers for THIS match count (see "generation" above).
            if generation == self.generation:
                # The AI crashed: show the error and stop the game.
                if isinstance(result, Exception):
                    self.error = tr("ai_error", error=str(result))
                    return
                # Keep the answer until the minimum delay has passed.
                self.pending = result
        # The answer is here AND "AI is thinking..." has been shown long enough:
        if self.pending is not None and now - self.turn_started >= config.AI_MIN_DELAY_SECONDS:
            # Unpack the move, and keep the statistics for the side panel.
            move, self.stats = self.pending
            # Safety check: the AI must choose a legal move.
            if move not in self.legal:
                self.error = tr("ai_error", error=tr("illegal"))
                return
            # Play the AI's move.
            self.state.apply_move(move)
            # Ready for the next AI turn.
            self.pending, self.working = None, False
            # Check if you must pass or the game ended.
            self.settle_turn(now)

    # Returns everything the keyboard can focus, in Tab order: your legal
    # cells first (only on your turn), then the buttons.
    # Called by handle_event() and draw().
    def targets(self) -> list[int | Button]:
        """Legal moves followed by match controls; overlay owns focus at the end."""
        # After game over, only the two buttons in the game-over box.
        if self.finished is not None:
            return [self.again_button, self.overlay_setup]
        # Your legal cells (only on your turn), then Restart and New Setup.
        return ((list(self.legal) if self.state.turn == config.PLAYER_COLOR else [])
                + [self.restart_button, self.setup_button])

    # Performs a target's action: a button or a cell.
    # Returns "setup" to tell main.py to go back to the setup screen.
    # Called by handle_event() for a click, or for Enter or Space.
    def activate(self, target: int | Button, now: float) -> str | None:
        """Return 'setup' when the outer application should change screen."""
        # New Setup: stop the AI and let main.py switch screens.
        if target is self.setup_button or target is self.overlay_setup:
            self.close()
            return "setup"
        # Restart or Play Again: a new match with the same seed.
        if target is self.restart_button or target is self.again_button:
            self.restart()
        # A legal cell on your turn: play it, then check pass / game over.
        elif (isinstance(target, int) and target in self.legal
              and self.state.turn == config.PLAYER_COLOR):
            self.state.apply_move(target)
            self.settle_turn(now)
        # Stay on this screen.
        return None

    # Reacts to one event. Called by main.py for every event.
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Ignore board clicks during AI work; controls remain responsive."""
        # The time this event is handled.
        now = perf_counter()
        # Was it your turn when the event arrived (before updating)?
        human_at_receipt = self.state.turn == config.PLAYER_COLOR
        # Expire the turn before accepting a click delivered after the deadline.
        # (If your time ran out, the timeout is applied first, so a late
        # click does not count.)
        self.update(now)
        # The things the keyboard can focus right now.
        targets = self.targets()
        # ---- Keyboard ----
        if event.type == pygame.KEYDOWN:
            # N shows or hides the cell numbers.
            if event.key == pygame.K_n:
                self.show_numbers = not self.show_numbers
            # Tab or Shift+Tab moves the focus.
            elif event.key == pygame.K_TAB:
                self.focus = tab_index(self.focus, len(targets), bool(event.mod & pygame.KMOD_SHIFT))
            # Enter or Space activates the focused target (if there is one).
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and 0 <= self.focus < len(targets):
                return self.activate(targets[self.focus], now)
        # ---- Left mouse click ----
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Buttons first: was one of them clicked?
            for target in targets:
                if isinstance(target, Button) and target.rect.collidepoint(event.pos):
                    return self.activate(target, now)
            # Board clicks count only during your turn, while the game is
            # running, and if the AI has not crashed.
            if (human_at_receipt and self.finished is None
                    and self.state.turn == config.PLAYER_COLOR and not self.error):
                # Which cell was clicked?
                move = self.renderer.hit_test(event.pos)
                # A legal move: play it.
                if move in self.legal:
                    return self.activate(move, now)
                # Clicked on the board, but not on a legal cell: explain.
                if self.renderer.rect.collidepoint(event.pos):
                    self.say(tr("illegal"), now)
        # Stay on this screen.
        return None

    # Draws the whole game screen. Called by main.py every frame.
    def draw(self, surface: pygame.Surface) -> None:
        """Render the board, scores, timer, search statistics and final overlay."""
        # The clocks freeze when the game is over.
        now = self.finished if self.finished is not None else perf_counter()
        # Clear the window.
        surface.fill(config.COLORS["background"])
        # The title at the top left.
        text(surface, tr("title"), (35, 19), config.FONT_HEADING)
        # The info line about the tile under the mouse.
        text(surface, self.renderer.hover_text(self.state), (370, 29), config.FONT_SMALL)
        # Find the focused cell or button, if any.
        targets = self.targets()
        focused = targets[self.focus] if 0 <= self.focus < len(targets) else None
        # Is it your turn?
        human = self.state.turn == config.PLAYER_COLOR
        # Draw the board. The legal-move rings appear only on your turn.
        # A focused cell (an int) is passed on; a focused button is not.
        self.renderer.draw(surface, self.state, self.legal if human and self.finished is None else {},
                           self.show_numbers, focused if isinstance(focused, int) else None)
        # The row of symbols under the board.
        self.renderer.legend(surface, 735)

        # ---- Side panel on the right ----
        # The panel's area and its background.
        panel = pygame.Rect(916, 18, 352, 706)
        pygame.draw.rect(surface, config.COLORS["panel"], panel, border_radius=8)
        # The left edge and width of the text inside the panel.
        x, width = 934, 318
        # Heading: "Game over", "Your turn" or "AI is thinking...".
        title = tr("over" if self.finished is not None else "player_turn" if human else "thinking")
        text(surface, title, (x, 36), config.FONT_HEADING, max_width=width)
        # Four lines: your points, the AI's points, the difference, and disc counts.
        lines = [tr("score", name=tr("player"), score=self.state.score(config.BLACK)),
                 tr("score", name=tr("ai"), score=self.state.score(config.WHITE)),
                 tr("difference",
                    difference=self.state.score(config.WHITE) - self.state.score(config.BLACK)),
                 tr("discs", black=self.state.disc_count(config.BLACK),
                    white=self.state.disc_count(config.WHITE))]
        # Draw them 29 pixels apart; the two scores in a bigger font.
        for i, label in enumerate(lines):
            text(surface, label, (x, 92 + i * 29),
                 config.FONT_BODY if i < 2 else config.FONT_SMALL, max_width=width)
        # The seed and the modifier range.
        text(surface, tr("seed", seed=self.settings.seed), (x, 218), config.FONT_SMALL, "muted",
             max_width=width)
        text(surface, tr("range_info"), (x, 244), config.FONT_SMALL, "muted")
        # The AI settings, for example "Minimax / depth 3" ("-" for Greedy's depth).
        depth = self.settings.depth if self.settings.algorithm == "minimax" else tr("na")
        text(surface, tr("config", algorithm=tr(self.settings.algorithm), depth=depth), (x, 270),
             config.FONT_SMALL, "muted")
        # The total game time.
        text(surface, tr("elapsed", seconds=now - self.started), (x, 306))
        # After game over: "Turn timer stopped".
        if self.finished is not None:
            text(surface, tr("timer_stopped"), (x, 338), color="muted")
        # On your turn: the countdown.
        elif human:
            limit = config.TURN_TIME_LIMIT_SECONDS
            # No time limit: say so.
            if limit is None:
                text(surface, tr("limit_off"), (x, 338), config.FONT_SMALL)
            else:
                # Seconds left (never below 0).
                remaining = max(0.0, limit - (now - self.turn_started))
                # Red during the last 10 seconds, gold before that.
                color = "red" if remaining <= config.TIMER_WARNING_SECONDS else "gold"
                # For example "Your time: 12.3 s".
                text(surface, tr("remaining", seconds=remaining), (x, 338), color=color)
                # A progress bar: an empty grey bar, then a coloured part
                # whose width matches the time left.
                pygame.draw.rect(surface, config.COLORS["disabled"], (x, 368, width, 7))
                pygame.draw.rect(surface, config.COLORS[color],
                                 (x, 368, round(width * remaining / limit), 7))
        # On the AI's turn: how long it has been thinking.
        else:
            text(surface, tr("ai_time", seconds=now - self.turn_started), (x, 338))
        # The "Last AI decision" section.
        text(surface, tr("ai_info"), (x, 400))
        # Before the AI's first move: "No AI move yet."
        if self.stats is None:
            text(surface, tr("no_decision"), (x, 432), config.FONT_SMALL, "muted")
        # Otherwise five lines of statistics (see AIStats in ai.py), 25 pixels apart.
        else:
            labels = (tr("chosen", number=self.stats.chosen_tile),
                      tr("evaluation", value=self.stats.evaluation),
                      tr("candidates", count=self.stats.candidates),
                      tr("nodes", count=self.stats.nodes),
                      tr("decision_time", ms=self.stats.time_ms))
            for i, label in enumerate(labels):
                text(surface, label, (x, 432 + i * 25), config.FONT_SMALL, max_width=width)
        # An AI error (red), or a message that has not expired yet (gold).
        if self.error or now < self.banner_until:
            wrapped_text(surface, self.error or self.banner, pygame.Rect(x, 575, width, 70),
                         "red" if self.error else "gold")
        # The Restart and New Setup buttons.
        self.restart_button.draw(surface, focused is self.restart_button)
        self.setup_button.draw(surface, focused is self.setup_button)

        # ---- Game-over box ----
        if self.finished is not None:
            # A see-through layer the size of the window (SRCALPHA allows
            # transparency), filled with black at 175 of 255 opacity, darkens
            # everything behind the box.
            shade = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 175))
            surface.blit(shade, (0, 0))
            # The box itself.
            pygame.draw.rect(surface, config.COLORS["panel"], (350, 232, 580, 320), border_radius=10)
            # BLACK, WHITE, or None for a draw.
            winner = self.state.winner()
            # "Player wins", "AI wins" or "Draw".
            result = tr("draw") if winner is None else tr(
                "winner", name=tr("player_short" if winner == config.PLAYER_COLOR else "ai_short"))
            # The result in big letters, centred.
            text(surface, result, (640, 279), config.FONT_TITLE, center=True)
            # Both scores and the difference (the first three panel lines).
            for i, label in enumerate(lines[:3]):
                text(surface, label, (640, 345 + i * 32), center=True)
            # The Play Again and New Setup buttons.
            self.again_button.draw(surface, focused is self.again_button)
            self.overlay_setup.draw(surface, focused is self.overlay_setup)
