"""Main simulator orchestrator"""
from __future__ import annotations

from typing import Dict, Optional

from ..board import BoardGeometry, BoardSetup
from ..bots import BotManager
from ..core import BankState, GamePhase, GameState, GameStatus, PlayerState, TurnState
from ..events import EventBus, GameEvent
from ..simulation.seeded_rng import SeededRng
from ..simulator.types.identifiers import PlayerId
from ..views import GameViewBuilder


class Simulator:
    """Top-level orchestrator for the game."""
    def __init__(self, seed: Optional[int] = None):
        self.rng = SeededRng(seed)
        self.game_state = GameState()
        self.game_state.game_id = f"game-{self.rng.seed}"
        self.game_state.seed = self.rng.seed
        self.game_state.phase = GamePhase.SETUP_FIRST
        self.game_state.status = GameStatus.ACTIVE
        self.board_geometry = BoardGeometry()
        self.game_state.board_state = BoardSetup.build_board_state(self.board_geometry, self.rng)
        self.game_state.bank_state = BankState()
        self.game_state.players = [PlayerState(player_id) for player_id in PlayerId.all_players()]
        self.game_state.turn_state = TurnState()
        self.game_state.turn_state.current_player = PlayerId.P1
        self.game_state.turn_state.turn_number = 1
        self.game_state.turn_state.phase = "PRE_ROLL"
        self.bot_manager = BotManager()
        self.event_bus = EventBus()

    def register_bots(self, bots: Dict[PlayerId, object]) -> None:
        """Register exactly four bots for the four players."""
        if set(bots.keys()) != set(PlayerId.all_players()):
            raise ValueError("Exactly one bot is required for each player.")
        for player_id, bot in bots.items():
            self.bot_manager.register_bot(player_id, bot)

    def build_view_for_player(self, player_id: PlayerId):
        """Build the current view for a specific player."""
        return GameViewBuilder(self.game_state).build_view(player_id)

    def start_game(self) -> GameState:
        """Notify every bot that the game has started and publish the initial public event."""
        if len(self.bot_manager.bots) != 4:
            raise ValueError("All four bots must be registered before starting the game.")

        for player_id in PlayerId.all_players():
            bot = self.bot_manager.get_bot(player_id)
            if hasattr(bot, "on_game_start"):
                bot.on_game_start(self.build_view_for_player(player_id))

        for player_id in PlayerId.all_players():
            self.event_bus.publish(
                GameEvent(
                    "GameStarted",
                    data={"seed": self.game_state.seed, "player_id": player_id.value},
                    game_id=self.game_state.game_id,
                    turn_number=self.game_state.turn_state.turn_number if self.game_state.turn_state else 0,
                    player_id=player_id,
                    visibility="PUBLIC",
                )
            )

        self.game_state.phase = GamePhase.SETUP_FIRST
        self.game_state.status = GameStatus.ACTIVE
        return self.game_state

    def run(self) -> None:
        """Execute a complete game."""
        pass
