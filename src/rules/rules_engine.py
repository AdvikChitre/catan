"""Rules engine"""
from ..core import GameState


class RulesEngine:
    """Rules engine for game logic queries"""
    def __init__(self, game_state: GameState):
        self.game_state = game_state
