"""Action-generation tests."""

from src.actions import ActionGenerator
from src.core.player_state import PlayerState
from src.core.game_state import GameState
from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import ResourceType


class TestActionGenerator:
    def test_pre_roll_actions_include_roll(self):
        sim = Simulator(seed=1)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        game = sim.game_state
        player = game.get_player(PlayerId.P1)
        player.resources[ResourceType.WOOD] = 0

        actions = ActionGenerator(game).get_available_actions(PlayerId.P1, "PRE_ROLL")

        assert any(action.action_type == "ROLL" for action in actions)

    def test_playing_actions_include_end_turn_and_build_actions(self):
        sim = Simulator(seed=2)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        game = sim.game_state
        player = game.get_player(PlayerId.P1)
        player.resources[ResourceType.WOOD] = 1
        player.resources[ResourceType.BRICK] = 1
        player.resources[ResourceType.SHEEP] = 1
        player.resources[ResourceType.WHEAT] = 1

        actions = ActionGenerator(game).get_available_actions(PlayerId.P1, "PLAYING")

        assert any(action.action_type == "END_TURN" for action in actions)
        assert any(action.action_type == "BUILD_SETTLEMENT" for action in actions)
