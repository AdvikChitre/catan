"""Game view - player-specific filtered state"""
from ..core import GameState
from ..simulator.types.identifiers import PlayerId


class GameView:
    """Player-specific immutable view of game state"""
    def __init__(self, game_state: GameState, player_id: PlayerId):
        self.game_state = game_state
        self.player_id = player_id
