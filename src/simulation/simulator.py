"""Main simulator orchestrator"""
from __future__ import annotations

from typing import Dict, List, Optional

from ..board import BoardGeometry, BoardSetup
from ..bots import BotManager
from ..core import BankState, BoardState, GamePhase, GameState, PlayerState, TurnState
from ..events import EventBus
from ..simulation.seeded_rng import SeededRng
from ..simulator.types.identifiers import PlayerId


class Simulator:
    """Top-level orchestrator for the game."""
    def __init__(self, seed: Optional[int] = None):
        self.rng = SeededRng(seed)
        self.game_state = GameState()
        self.game_state.game_id = f"game-{self.rng.seed}"
        self.game_state.seed = self.rng.seed
        self.game_state.phase = GamePhase.SETUP_FIRST
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

    def run(self) -> None:
        """Execute a complete game."""
        pass
