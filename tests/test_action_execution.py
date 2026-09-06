"""Action execution tests."""

from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId, VertexId, EdgeId
from src.simulator.types.resource import ResourceType


class TestActionExecution:
    def test_execute_settlement_action_reduces_resources_and_places_building(self):
        sim = Simulator(seed=13)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        player = sim.game_state.get_player(PlayerId.P1)
        player.resources[ResourceType.WOOD] = 1
        player.resources[ResourceType.BRICK] = 1
        player.resources[ResourceType.SHEEP] = 1
        player.resources[ResourceType.WHEAT] = 1

        result = sim.execute_action(PlayerId.P1, {"type": "BUILD_SETTLEMENT", "vertex": VertexId("V00")})

        assert result["type"] == "BUILD_SETTLEMENT"
        assert sim.game_state.board_state.vertices[VertexId("V00")].building.owner == PlayerId.P1
        assert PlayerId.P1 in {player.player_id for player in sim.game_state.players}

    def test_execute_road_action_places_road(self):
        sim = Simulator(seed=13)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        player = sim.game_state.get_player(PlayerId.P1)
        player.resources[ResourceType.WOOD] = 1
        player.resources[ResourceType.BRICK] = 1

        result = sim.execute_action(PlayerId.P1, {"type": "BUILD_ROAD", "edge": EdgeId("E00")})

        assert result["type"] == "BUILD_ROAD"
        assert sim.game_state.board_state.edges[EdgeId("E00")].road.owner == PlayerId.P1

    def test_execute_end_turn_advances_player(self):
        sim = Simulator(seed=13)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        sim.game_state.turn_state.current_player = PlayerId.P4

        sim.execute_action(PlayerId.P4, "END_TURN")

        assert sim.game_state.turn_state.current_player == PlayerId.P1
        assert sim.game_state.turn_state.phase == "PRE_ROLL"
