"""Victory and scoring tests."""

from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import DevelopmentCardType
from src.core.building import EdgeState, Road


class TestVictory:
    def test_victory_points_include_settlements_cities_and_largest_army(self):
        sim = Simulator(seed=11)
        p1 = sim.game_state.get_player(PlayerId.P1)
        p1.settlements = {"V00", "V01", "V02"}
        p1.cities = {"V10", "V11"}
        p1.development_cards[DevelopmentCardType.VICTORY_POINT] = 2
        p1.largest_army_count = 3

        sim._recalculate_victory_points()

        assert p1.has_largest_army is True
        assert p1.get_calculated_victory_points() == 11
        assert sim.check_victory() == PlayerId.P1
        assert sim.game_state.status.value == "COMPLETED"

    def test_longest_road_achievement_requires_a_long_connected_path(self):
        sim = Simulator(seed=12)
        p1 = sim.game_state.get_player(PlayerId.P1)
        board = sim.game_state.board_state

        for edge_id in ["E00", "E01", "E02", "E03", "E04"]:
            board.edges[edge_id] = EdgeState(edge_id, Road(owner=p1.player_id))

        sim._recalculate_victory_points()

        assert p1.has_longest_road is True
