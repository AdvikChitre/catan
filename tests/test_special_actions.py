import pytest
from tests.engine_helpers import setup,playing,grant,apply,option
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import DevelopmentCardType as D, ResourceType as R


def card(sim,kind):
    sim.development_deck.remove(kind);sim.bank.development_cards[kind]-=1
    sim.player(sim.active).development_cards[kind]+=1


def test_knight_uses_same_choice_api_and_returns_to_pre_roll():
    s=setup();card(s,D.KNIGHT)
    apply(s,'PLAY_DEVELOPMENT_CARD',card='KNIGHT')
    assert s.stage=='ROBBER'
    actions=s.available_actions()
    assert all(a['tile']!=s.board.robber_tile_id for a in actions)
    for a in actions:
        if a['victim']:assert PlayerId(a['victim']) in s._victims(a['tile'],s.active)
    a=actions[0];s.apply_action(s.active,a)
    assert s.board.robber_tile_id==a['tile'] and s.stage=='PRE_ROLL'
    assert not any(a['type']=='PLAY_DEVELOPMENT_CARD' for a in s.available_actions())
    s.assert_invariants()


def test_year_of_plenty_accepts_two_of_same_resource():
    s=playing();card(s,D.YEAR_OF_PLENTY);before=s.player(s.active).resources[R.WOOD]
    apply(s,'PLAY_DEVELOPMENT_CARD',card='YEAR_OF_PLENTY')
    with pytest.raises(ValueError):apply(s,'TAKE_RESOURCES',resources={'WOOD':2,'BRICK':3})
    apply(s,'TAKE_RESOURCES',resources={'WOOD':2})
    assert s.player(s.active).resources[R.WOOD]==before+2
    s.assert_invariants()


def test_monopoly_collects_resource_without_changing_total():
    s=playing();card(s,D.MONOPOLY);grant(s,PlayerId.P2,{'ORE':2});grant(s,PlayerId.P3,{'ORE':1})
    before=sum(p.resources[R.ORE] for p in s.game_state.players)
    apply(s,'PLAY_DEVELOPMENT_CARD',card='MONOPOLY');apply(s,'TAKE_MONOPOLY',resource='ORE')
    assert s.player(s.active).resources[R.ORE]==before
    s.assert_invariants()


def test_free_roads_recalculate_options_and_do_not_charge_resources():
    s=playing();card(s,D.ROAD_BUILDING);p=s.player(s.active);before=p.resources.copy();roads=len(p.roads)
    apply(s,'PLAY_DEVELOPMENT_CARD',card='ROAD_BUILDING')
    a=option(s,'BUILD_FREE_ROAD');s.apply_action(s.active,a)
    assert a not in s.available_actions()
    s.apply_action(s.active,option(s,'BUILD_FREE_ROAD'))
    assert len(p.roads)==roads+2 and p.resources==before and s.stage=='PLAYING'
    s.assert_invariants()


def test_bank_trade_uses_port_ratio_and_returns_cards():
    s=playing();grant(s,s.active,{'WOOD':4})
    a=next(a for a in s.available_actions() if a['type']=='BANK_TRADE' and a['give_resource']=='WOOD')
    before=s.player(s.active).resources[R.WOOD]
    s.apply_action(s.active,a)
    assert s.player(s.active).resources[R.WOOD]==before-a['ratio']
    s.assert_invariants()
