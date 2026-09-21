import pytest
from src.bots import BotManager
from src.player import Player
from src.simulator.types.identifiers import PlayerId

def test_registry_accepts_players_and_rejects_unrelated_objects():
    m=BotManager()
    for pid in PlayerId.all_players():m.register_bot(pid,Player())
    assert len(m.get_all_bots())==4
    with pytest.raises(TypeError):m.register_bot(PlayerId.P1,object())
