"""Compatibility registry for trusted local players. Execution uses ProcessPlayer."""
from ..player import Player
from ..simulator.types.identifiers import PlayerId

class BotManager:
    def __init__(self): self.bots={}
    def register_bot(self,player_id,player):
        if not isinstance(player,Player): raise TypeError('Implement Player')
        self.bots[player_id]=player
    def get_bot(self,player_id): return self.bots[player_id]
    def get_all_bots(self): return [self.bots[p] for p in PlayerId.all_players() if p in self.bots]
