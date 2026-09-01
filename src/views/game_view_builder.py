"""Game view builder"""
from ..core import GameState
from ..simulator.types.identifiers import PlayerId
from .game_view import GameView


class GameViewBuilder:
    """Builds player-specific game views with hidden information filtering"""
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def build_view(self, player_id: PlayerId) -> GameView:
        """Build a filtered view for the given player"""
        return GameView(self.game_state, player_id)
