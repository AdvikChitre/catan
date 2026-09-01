"""Action generator"""
from typing import List
from ..core import GameState
from ..simulator.types.identifiers import PlayerId
from .action_types import AvailableAction


class ActionGenerator:
    """Generates legal available actions for a bot"""
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def get_available_actions(
        self, player_id: PlayerId, phase: str
    ) -> List[AvailableAction]:
        """Get available actions for a player in the given phase"""
        return []
