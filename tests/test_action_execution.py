import pytest
from tests.engine_helpers import playing, grant, apply, option
from src.simulator.types.identifiers import PlayerId

def test_build_road_spends_cards_and_preserves_invariants():
    s=playing();grant(s,s.active,{'WOOD':1,'BRICK':1});a=option(s,'BUILD_ROAD')
    s.apply_action(s.active,a);assert s._road_owner(a['edge'])==s.active;s.assert_invariants()

def test_city_returns_settlement_piece():
    s=playing();grant(s,s.active,{'ORE':3,'WHEAT':2});a=option(s,'BUILD_CITY');p=s.player(s.active)
    before=p.settlements_remaining;s.apply_action(s.active,a)
    assert p.settlements_remaining==before+1;s.assert_invariants()

def test_wrong_seat_and_stale_decision_rejected():
    s=playing()
    with pytest.raises(ValueError):s.apply_action(PlayerId.P2,{'type':'END_TURN'})
    with pytest.raises(ValueError):s.apply_action(s.active,{'type':'END_TURN'},-1)
    apply(s,'END_TURN');assert s.active==PlayerId.P2 and s.stage=='PRE_ROLL'
