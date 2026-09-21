import pytest
from src.player import Player, thaw
from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import DevelopmentCardType as D
from tests.engine_helpers import setup, playing, grant, apply, option


def test_observations_are_detached_private_and_complete():
    sim=setup()
    sim.player(PlayerId.P2).development_cards[D.VICTORY_POINT]=2
    view=sim.build_view_for_player(PlayerId.P1)
    assert len(view.board.vertices)==54 and len(view.board.edges)==72
    assert 'game_state' not in view
    opponent=next(p for p in view.opponents if p.player_id=='P2')
    assert opponent.victory_points==2
    assert 'resources' not in opponent and 'development_cards' not in opponent
    with pytest.raises(TypeError): view.self.resources['WOOD']=100
    before=view.self.resource_count
    grant(sim,PlayerId.P1,{'WOOD':1})
    assert view.self.resource_count==before


def test_events_delivered_before_choice_and_one_instance_per_seat():
    class Observer(Player):
        def __init__(self): self.events=[]
        def on_event(self,event): self.events.append(event)
        def choose_action(self,view,options):
            assert self.events[0].type=='GameStarted'
            return options[0]
    sim=Simulator(1);players={p:Observer() for p in PlayerId.all_players()}
    sim.register_players(players);sim.step()
    assert all(p.events[-1].type=='SettlementBuilt' for p in players.values())
    assert len({id(p.events) for p in players.values()})==4
    with pytest.raises(ValueError): Simulator(1).register_players({p:players[PlayerId.P1] for p in PlayerId.all_players()})


def test_failed_event_handler_does_not_hide_event_from_other_players():
    class Broken(Player):
        def on_event(self,e): raise RuntimeError('broken')
    class Observer(Player):
        def __init__(self): self.events=[]
        def on_event(self,e): self.events.append(e.type)
    sim=Simulator(1);players={p:Observer() for p in PlayerId.all_players()};players[PlayerId.P1]=Broken()
    sim.register_players(players);sim.start_game()
    assert sim.result['status']=='player_failed'
    assert players[PlayerId.P2].events==['GameStarted','GameEnded']


def test_trade_is_generic_and_one_round_with_counter_and_revalidation():
    sim=playing();pid=sim.active
    grant(sim,pid,{'WOOD':3});grant(sim,PlayerId.P2,{'ORE':2});grant(sim,PlayerId.P3,{'ORE':2})
    assert option(sim,'TRADE')=={'type':'TRADE'}
    apply(sim,'TRADE',recipients=['P3','P2'],give={'WOOD':1},receive={'ORE':1})
    assert sim.acting_player()==PlayerId.P2
    apply(sim,'ACCEPT')
    assert sim.acting_player()==PlayerId.P3
    apply(sim,'COUNTER',give={'ORE':2},receive={'WOOD':2})
    assert sim.stage=='TRADE_SELECT' and sim.acting_player()==pid
    before=sim.player(pid).resources.copy()
    apply(sim,'SELECT_TRADE',response=1)
    from src.simulator.types.resource import ResourceType as R
    assert sim.player(pid).resources[R.WOOD]==before[R.WOOD]-2
    assert sim.player(pid).resources[R.ORE]==before[R.ORE]+2
    assert sim.stage=='PLAYING'
    sim.assert_invariants()


@pytest.mark.parametrize('action',[
    {'type':'TRADE','recipients':['P2'],'give':{'WOOD':-1},'receive':{'ORE':1}},
    {'type':'TRADE','recipients':['P1'],'give':{'WOOD':1},'receive':{'ORE':1}},
    {'type':'TRADE','recipients':['P2'],'give':{'WOOD':True},'receive':{'ORE':1}},
    {'type':'BUILD_ROAD','edge':'missing'},
    {'type':'BANK_TRADE','give_resource':'WOOD','receive_resource':'ORE','ratio':0},
])
def test_invalid_actions_do_not_mutate_state_or_publish(action):
    sim=playing();grant(sim,sim.active,{'WOOD':3})
    before=thaw(sim.build_view_for_player(sim.active));events=len(sim.event_bus.events)
    with pytest.raises(ValueError): sim.apply_action(sim.active,action)
    assert thaw(sim.build_view_for_player(sim.active))==before
    assert len(sim.event_bus.events)==events


def test_private_draw_is_not_sent_to_opponents():
    sim=playing();grant(sim,sim.active,{'ORE':1,'WHEAT':1,'SHEEP':1})
    apply(sim,'BUY_DEVELOPMENT_CARD')
    events=sim.event_bus.events[-2:]
    draw=next(e for e in events if e.event_type=='DevelopmentCardDrawn')
    assert draw.is_visible_to(sim.active)
    assert not draw.is_visible_to(PlayerId.P2)
