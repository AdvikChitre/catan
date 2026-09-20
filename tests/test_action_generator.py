from tests.engine_helpers import setup,playing,grant
from src.actions.action_generator import ActionGenerator

def test_pre_roll_has_roll_but_no_end_turn():
    s=setup();actions=ActionGenerator(s).get_available_actions(s.active,'PRE_ROLL')
    assert {'type':'ROLL'} in actions and {'type':'END_TURN'} not in actions

def test_generator_delegates_real_legality():
    s=playing();grant(s,s.active,{'WOOD':1,'BRICK':1})
    actions=ActionGenerator(s).get_available_actions(s.active)
    assert actions==s.available_actions()
    assert all(s.can_build_road(s.active,a['edge']) for a in actions if a['type']=='BUILD_ROAD')
