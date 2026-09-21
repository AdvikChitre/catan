from src.simulation import Simulator
from src.player.example import ExamplePlayer
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import ResourceType as R


def setup(seed=42):
    sim=Simulator(seed)
    sim.register_players({p:ExamplePlayer() for p in PlayerId.all_players()})
    sim.start_game()
    while sim.stage.startswith('SETUP'): sim.step()
    sim.assert_invariants()
    return sim


def playing(seed=42):
    sim=setup(seed)
    while sim.stage!='PLAYING': sim.step()
    return sim


def grant(sim,pid,resources):
    # Test fixture transfers through the bank, maintaining conservation.
    sim._grant(pid,{R(k) if isinstance(k,str) else k:n for k,n in resources.items()})


def apply(sim,kind,**payload):
    return sim.apply_action(sim.acting_player(),{'type':kind,**payload},sim.decision_number)


def option(sim,kind):
    return next(a for a in sim.available_actions() if a['type']==kind)
