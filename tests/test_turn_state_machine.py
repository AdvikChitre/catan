"""Normal turn-state-machine tests."""

from src.core.building import Building, TileState, VertexState
from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId, TileId, VertexId
from src.simulator.types.resource import ResourceType


class TestTurnStateMachine:
    def test_roll_dice_updates_turn_state(self):
        sim = Simulator(seed=5)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        sim.game_state.turn_state.current_player = PlayerId.P2

        total = sim.roll_dice()

        assert 2 <= total <= 12
        assert sim.game_state.turn_state.dice_roll == total
        assert sim.game_state.turn_state.phase == "PLAYING"

    def test_resolve_roll_awards_resources_to_settlement_owner(self):
        sim = Simulator(seed=9)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        sim.game_state.board_state.tiles.clear()

        tile_id = TileId("T00")
        vertex_id = VertexId("V00")
        sim.game_state.board_state.tiles[tile_id] = TileState(str(tile_id), ResourceType.WOOD, 6, False)
        sim.game_state.board_state.vertices[vertex_id] = VertexState(str(vertex_id), Building.settlement(PlayerId.P1))
        sim.board_geometry.get_tile(tile_id).vertex_ids.add(vertex_id)

        sim._resolve_roll(6)

        assert sim.game_state.get_player(PlayerId.P1).resources[ResourceType.WOOD] >= 1

    def test_end_turn_advances_player_order(self):
        sim = Simulator(seed=11)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        sim.game_state.turn_state.current_player = PlayerId.P4

        sim.end_turn()

        assert sim.game_state.turn_state.current_player == PlayerId.P1
        assert sim.game_state.turn_state.turn_number == 2
        assert sim.game_state.turn_state.phase == "PRE_ROLL"
