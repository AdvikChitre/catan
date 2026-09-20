from src.player import Player
from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId

def test_invalid_action_ends_match_instead_of_silently_substituting_strategy():
    class Invalid(Player):
        def choose_action(self,view,options):return {'type':'NOT_AN_ACTION'}
    s=Simulator(3);s.register_players({p:Invalid() for p in PlayerId.all_players()})
    assert s.run()['status']=='player_failed'
    assert not s.board.vertices
