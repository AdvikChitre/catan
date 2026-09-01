"""Main simulator orchestrator"""
from typing import List, Optional
from ..core import GameState
from ..board import BoardGeometry
from ..bots import BotManager
from ..events import EventBus
from ..simulation.seeded_rng import SeededRng
from ..simulator.types.identifiers import PlayerId


class Simulator:
    """Top-level orchestrator for the game"""
    def __init__(self, seed: Optional[int] = None):
        self.rng = SeededRng(seed)
        self.game_state = GameState()
        self.game_state.seed = self.rng.seed
        self.board_geometry = BoardGeometry()
        self.bot_manager = BotManager()
        self.event_bus = EventBus()

    def register_bots(self, bots: dict) -> None:
        """Register bots for all four players"""
        for player_id, bot in bots.items():
            self.bot_manager.register_bot(player_id, bot)

    def run(self) -> None:
        """Execute a complete game"""
        pass
