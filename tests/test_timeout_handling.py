"""Bot timeout and fallback handling tests."""

import time

from src.bots import BotInterface, BotManager
from src.simulation import Simulator
from src.simulator.types.identifiers import PlayerId


class SlowBot(BotInterface):
    def on_game_start(self, view) -> None:
        pass

    def take_turn(self, view, available_actions):
        time.sleep(0.2)
        return available_actions[0]

    def on_event(self, event: dict) -> None:
        pass


class ExplodingBot(BotInterface):
    def on_game_start(self, view) -> None:
        raise RuntimeError("boom")

    def take_turn(self, view, available_actions):
        raise RuntimeError("boom")

    def on_event(self, event: dict) -> None:
        pass


class InvalidActionBot(BotInterface):
    def on_game_start(self, view) -> None:
        pass

    def take_turn(self, view, available_actions):
        return "NOT_A_REAL_ACTION"

    def on_event(self, event: dict) -> None:
        pass


class TestBotSafety:
    def test_call_bot_times_out_and_returns_default(self):
        manager = BotManager(timeout_seconds=0.01)
        manager.register_bot(PlayerId.P1, SlowBot())

        result = manager.call_bot(PlayerId.P1, "take_turn", None, ["ROLL"], default="ROLL", fallback="ROLL")

        assert result == "ROLL"

    def test_call_bot_catches_exceptions(self):
        manager = BotManager(timeout_seconds=0.1)
        manager.register_bot(PlayerId.P1, ExplodingBot())

        result = manager.call_bot(PlayerId.P1, "on_game_start", None, default=None, fallback=None)

        assert result is None

    def test_simulator_falls_back_when_bot_returns_invalid_turn_action(self):
        sim = Simulator(seed=99)
        sim.register_bots({pid: InvalidActionBot() for pid in PlayerId.all_players()})
        sim.game_state.turn_state.current_player = PlayerId.P1
        sim.game_state.turn_state.phase = "PRE_ROLL"

        sim.take_turn_for_current_player()

        assert sim.game_state.turn_state.current_player in PlayerId.all_players()
        assert sim.game_state.turn_state.phase == "PRE_ROLL"
