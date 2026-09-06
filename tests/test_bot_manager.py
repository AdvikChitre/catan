"""Bot manager and dummy bot tests."""

from src.bots import BotManager
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId


class TestBotManager:
    def test_registers_all_players(self):
        manager = BotManager()
        for player_id in PlayerId.all_players():
            manager.register_bot(player_id, DummyBot())

        assert len(manager.get_all_bots()) == 4
        assert manager.get_bot(PlayerId.P1).__class__ is DummyBot

    def test_dummy_bot_returns_first_action(self):
        bot = DummyBot()
        first = bot.take_turn(view=None, available_actions=["ROLL", "END_TURN"])
        assert first == "ROLL"
