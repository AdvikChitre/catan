"""Compatibility facade for the player snapshot projection."""
from .observation import observation
class GameViewBuilder:
    def __init__(self, simulator): self.simulator=simulator
    def build_view(self, player_id): return observation(self.simulator,player_id)
