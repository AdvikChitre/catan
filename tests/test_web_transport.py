"""Tests for the minimal web transport helpers."""

from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId
from src.web_transport import server


def test_get_replay_and_state_snapshots():
    sim = Simulator(seed=7)
    bots = {pid: DummyBot() for pid in PlayerId.all_players()}
    sim.register_bots(bots)
    sim.start_game()

    replay = server.get_replay(sim)
    assert "metadata" in replay and "events" in replay

    public_state = server.get_state(sim)
    assert public_state["game_id"] == sim.game_state.game_id

    p1_state = server.get_state(sim, PlayerId.P1)
    assert p1_state["player_id"] == PlayerId.P1.value
    assert "resources" in p1_state
