"""Initial simulator setup tests."""

from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId
from src.simulator.run import DummyBot


class TestSimulatorSetup:
    def test_simulator_initializes_players_and_board(self):
        sim = Simulator(seed=42)

        assert sim.game_state.seed == 42
        assert len(sim.game_state.players) == 4
        assert sim.game_state.turn_state.current_player == PlayerId.P1
        assert sim.game_state.board_state is not None
        assert len(sim.game_state.board_state.tiles) == 19

    def test_register_bots_requires_all_players(self):
        sim = Simulator(seed=9)
        bots = {PlayerId.P1: DummyBot(), PlayerId.P2: DummyBot(), PlayerId.P3: DummyBot()}

        try:
            sim.register_bots(bots)
            assert False, "Expected ValueError for incomplete bot registration"
        except ValueError:
            pass
