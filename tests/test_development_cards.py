"""Basic development-card purchase tests."""

from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import ResourceType


class TestDevelopmentCards:
    def test_buy_development_card_draws_from_seeded_deck(self):
        sim = Simulator(seed=42)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
        player = sim.game_state.get_player(PlayerId.P1)
        player.resources[ResourceType.WHEAT] = 1
        player.resources[ResourceType.SHEEP] = 1
        player.resources[ResourceType.ORE] = 1

        card = sim.buy_development_card(PlayerId.P1)

        assert card in sim.game_state.bank_state.development_cards
        assert player.development_cards[card] >= 1
        assert sim.game_state.bank_state.development_cards[card] >= 0

    def test_buy_development_card_requires_resources(self):
        sim = Simulator(seed=42)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})

        try:
            sim.buy_development_card(PlayerId.P1)
            assert False, "Expected ValueError when resources are insufficient"
        except ValueError:
            pass
