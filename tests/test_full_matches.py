import hashlib
import json
import os
import subprocess
import sys
import pytest
from src.simulation import Simulator
from src.simulation.simulator import GameConfig
from src.player.example import ExamplePlayer
from src.simulator.types.identifiers import PlayerId
from src.platform.recording import RecordingSimulator


@pytest.mark.parametrize('seed',[1,2,3,4,5,42])
def test_complete_matches_conserve_resources_and_pieces(seed):
    s=Simulator(seed)
    s.register_players({p:ExamplePlayer() for p in PlayerId.all_players()})
    s.subscribe(lambda _:s.assert_invariants())
    result=s.run()
    assert result['status']=='completed',result
    assert s.player(s.game_state.winner).victory_points>=10
    assert s.decision() is None


def test_same_decisions_reproduce_game_without_calling_players():
    a=Simulator(42);a.register_players({p:ExamplePlayer() for p in PlayerId.all_players()});a.run()
    b=Simulator(42);b.register_players({p:ExamplePlayer() for p in PlayerId.all_players()});b.start_game()
    for entry in a.decisions:b.apply_action(entry['player_id'],entry['action'],entry['decision'])
    assert a.result==b.result
    assert [(e.event_type,e.data) for e in a.event_bus.events]==[(e.event_type,e.data) for e in b.event_bus.events]


def test_configured_limit_is_not_a_victory():
    s=Simulator(42,GameConfig(max_turns=1));s.register_players({p:ExamplePlayer() for p in PlayerId.all_players()})
    assert s.run()['status']=='stopped' and s.game_state.winner is None


def test_cross_process_hash_seed_does_not_change_decisions():
    code='''import json,hashlib
from src.simulation import Simulator
from src.player.example import ExamplePlayer
from src.simulator.types.identifiers import PlayerId
s=Simulator(7);s.register_players({p:ExamplePlayer() for p in PlayerId.all_players()});s.run()
print(hashlib.sha256(json.dumps(s.decisions,sort_keys=True).encode()).hexdigest())
'''
    hashes=[]
    for seed in ['1','9876']:
        env=dict(os.environ,PYTHONHASHSEED=seed)
        hashes.append(subprocess.check_output([sys.executable,'-c',code],env=env,text=True,timeout=30))
    assert hashes[0]==hashes[1]
