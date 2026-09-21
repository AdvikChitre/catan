import pytest
from tests.engine_helpers import setup,apply
from src.simulator.types.identifiers import PlayerId

def test_roll_required_then_turn_ends():
    s=setup()
    with pytest.raises(ValueError):apply(s,'END_TURN')
    apply(s,'ROLL');assert 2<=s.game_state.turn_state.dice_roll<=12
    while s.stage!='PLAYING':s.step()
    apply(s,'END_TURN');assert s.active==PlayerId.P2
    assert s.game_state.turn_state.turn_number==2 and s.stage=='PRE_ROLL'

def test_roll_cannot_be_repeated():
    s=setup();apply(s,'ROLL')
    with pytest.raises(ValueError):apply(s,'ROLL')
