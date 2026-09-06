"""Tests for game-start notifications and setup phase transitions."""

from src.simulation import Simulator
from src.simulation.simulator import Simulator as SimulatorImpl
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId


class RecordingBot(DummyBot):
    def __init__(self):
        self.started_for = []

    def on_game_start(self, view):
        self.started_for.append(view.player_id)


class TestSimulatorStart:
    def test_start_game_notifies_each_bot_once(self):
        sim = SimulatorImpl(seed=17)
        bots = {pid: RecordingBot() for pid in PlayerId.all_players()}
        sim.register_bots(bots)

        sim.start_game()

        assert [bot.started_for[0] for bot in bots.values()] == [PlayerId.P1, PlayerId.P2, PlayerId.P3, PlayerId.P4]
        assert sim.game_state.turn_state.current_player == PlayerId.P1
        assert sim.event_bus.events[0].event_type == "GameStarted"

    def test_start_game_raises_when_bots_are_missing(self):
        sim = Simulator(seed=9)

        try:
            sim.register_bots({PlayerId.P1: DummyBot(), PlayerId.P2: DummyBot(), PlayerId.P3: DummyBot()})
            assert False, "Expected ValueError from incomplete bot registration"
        except ValueError:
            pass
