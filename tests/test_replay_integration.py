"""Replay recorder integration tests."""

from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId
from src.simulator.run import DummyBot


def test_replay_recorder_records_game_started_and_events():
    sim = Simulator(seed=12345)
    # recorder exists and has metadata
    assert hasattr(sim, "replay_recorder")
    assert sim.replay_recorder.metadata.get("seed") == sim.game_state.seed
    assert sim.replay_recorder.metadata.get("game_id") == sim.game_state.game_id

    # register dummy bots and start game to generate events
    bots = {pid: DummyBot() for pid in PlayerId.all_players()}
    sim.register_bots(bots)
    sim.start_game()

    # after starting, recorder should have recorded GameStarted events for each player
    recorded = sim.replay_recorder.events
    assert len(recorded) >= 4
    types = [e.event_type for e in recorded]
    assert "GameStarted" in types

    exported = sim.replay_recorder.export()
    assert "metadata" in exported and "events" in exported
    assert exported["metadata"]["game_id"] == sim.game_state.game_id
