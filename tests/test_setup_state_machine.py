"""Setup-state machine tests."""

from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId
from src.simulator.run import DummyBot


class SequenceBot(DummyBot):
    def choose_initial_placement(self, view, options):
        return options[0]


class TestSetupStateMachine:
    def test_setup_round_places_two_settlements_and_roads_per_player(self):
        sim = Simulator(seed=123)
        sim.register_bots({pid: SequenceBot() for pid in PlayerId.all_players()})

        sim.perform_setup()

        for player in sim.game_state.players:
            assert len(player.settlements) == 2
            assert len(player.roads) == 2
            assert player.settlements_remaining == 3
            assert player.roads_remaining == 13

        assert len(sim.game_state.board_state.vertices) == 8
        assert len(sim.game_state.board_state.edges) == 8
        assert sim.game_state.phase.value == "NORMAL_PLAY"

    def test_second_setup_pass_awards_starting_resources(self):
        sim = Simulator(seed=7)
        sim.register_bots({pid: SequenceBot() for pid in PlayerId.all_players()})

        sim.perform_setup()

        total_resources = sum(
            player.get_total_resources() for player in sim.game_state.players
        )
        assert total_resources > 0
        for player in sim.game_state.players:
            assert player.get_total_resources() >= 0
