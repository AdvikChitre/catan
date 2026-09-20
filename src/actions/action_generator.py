"""Compatibility facade; legality has a single implementation in RulesEngine."""
class ActionGenerator:
    def __init__(self, simulator): self.simulator=simulator
    def get_available_actions(self, player_id, phase=None):
        if self.simulator.result or player_id!=self.simulator.acting_player(): return []
        if phase is not None and phase!=self.simulator.stage: return []
        return self.simulator.available_actions()
