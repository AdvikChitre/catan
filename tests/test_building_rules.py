"""Basic building-rule validation tests."""

from src.core.building import Building, VertexState
from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId, VertexId
from src.simulator.types.resource import ResourceType


class TestBuildingRules:
    def test_can_build_settlement_requires_resources_and_space(self):
        sim = Simulator(seed=42)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        player = sim.game_state.get_player(PlayerId.P1)
        player.resources[ResourceType.WOOD] = 1
        player.resources[ResourceType.BRICK] = 1
        player.resources[ResourceType.SHEEP] = 1
        player.resources[ResourceType.WHEAT] = 1

        assert sim.can_build_settlement(PlayerId.P1, VertexId("V00")) is True

    def test_can_build_city_requires_existing_settlement(self):
        sim = Simulator(seed=42)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        player = sim.game_state.get_player(PlayerId.P1)
        sim.game_state.board_state.vertices[VertexId("V00")] = VertexState("V00", Building.settlement(PlayerId.P1))
        player.resources[ResourceType.WHEAT] = 2
        player.resources[ResourceType.ORE] = 3

        assert sim.can_build_city(PlayerId.P1, VertexId("V00")) is True

    def test_can_buy_development_card_requires_three_resources(self):
        sim = Simulator(seed=42)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        player = sim.game_state.get_player(PlayerId.P1)
        player.resources[ResourceType.WHEAT] = 1
        player.resources[ResourceType.SHEEP] = 1
        player.resources[ResourceType.ORE] = 1

        assert sim.can_buy_development_card(PlayerId.P1) is True
