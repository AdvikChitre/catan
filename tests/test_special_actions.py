"""Tests for robber moves and special development-card actions."""

from src.simulation import Simulator
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import DevelopmentCardType, ResourceType


class TestSpecialActions:
    def test_play_knight_moves_robber_and_steals(self):
        sim = Simulator(seed=7)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})

        p1 = sim.game_state.get_player(PlayerId.P1)
        p2 = sim.game_state.get_player(PlayerId.P2)
        p1.development_cards[DevelopmentCardType.KNIGHT] = 1
        p2.resources[ResourceType.WOOD] = 2
        p2.resources[ResourceType.BRICK] = 1

        robber_tile = sim.game_state.board_state.robber_tile_id
        target_tile = next(
            tile_id for tile_id, tile in sim.game_state.board_state.tiles.items()
            if tile_id != robber_tile and tile.resource_type is not None
        )

        result = sim.play_development_card(PlayerId.P1, DevelopmentCardType.KNIGHT, tile_id=target_tile, victim_id=PlayerId.P2)

        assert result["type"] == "PLAY_KNIGHT"
        assert sim.game_state.board_state.robber_tile_id == target_tile
        assert sim.game_state.board_state.tiles[target_tile].has_robber is True
        assert p1.resources[ResourceType.WOOD] == 1
        assert p2.resources[ResourceType.WOOD] == 1

    def test_play_year_of_plenty_gives_two_resources(self):
        sim = Simulator(seed=8)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})

        p1 = sim.game_state.get_player(PlayerId.P1)
        p1.development_cards[DevelopmentCardType.YEAR_OF_PLENTY] = 1
        sim.game_state.bank_state.resources[ResourceType.WOOD] = 10
        sim.game_state.bank_state.resources[ResourceType.BRICK] = 10

        sim.play_development_card(
            PlayerId.P1,
            DevelopmentCardType.YEAR_OF_PLENTY,
            resources={ResourceType.WOOD: 1, ResourceType.BRICK: 1},
        )

        assert p1.resources[ResourceType.WOOD] == 1
        assert p1.resources[ResourceType.BRICK] == 1
        assert sim.game_state.bank_state.resources[ResourceType.WOOD] == 9
        assert sim.game_state.bank_state.resources[ResourceType.BRICK] == 9

    def test_play_monopoly_steals_all_matching_cards_from_opponents(self):
        sim = Simulator(seed=9)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})

        p1 = sim.game_state.get_player(PlayerId.P1)
        p2 = sim.game_state.get_player(PlayerId.P2)
        p3 = sim.game_state.get_player(PlayerId.P3)
        p1.development_cards[DevelopmentCardType.MONOPOLY] = 1
        p2.resources[ResourceType.WOOD] = 2
        p3.resources[ResourceType.WOOD] = 1

        sim.play_development_card(PlayerId.P1, DevelopmentCardType.MONOPOLY, resource_type=ResourceType.WOOD)

        assert p1.resources[ResourceType.WOOD] == 3
        assert p2.resources[ResourceType.WOOD] == 0
        assert p3.resources[ResourceType.WOOD] == 0

    def test_bank_trade_exchanges_four_for_one(self):
        sim = Simulator(seed=10)
        sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})

        p1 = sim.game_state.get_player(PlayerId.P1)
        p1.resources[ResourceType.WOOD] = 4
        sim.game_state.bank_state.resources[ResourceType.BRICK] = 10

        result = sim.bank_trade(PlayerId.P1, ResourceType.WOOD, ResourceType.BRICK)

        assert result["type"] == "BANK_TRADE"
        assert p1.resources[ResourceType.WOOD] == 0
        assert p1.resources[ResourceType.BRICK] == 1
        assert sim.game_state.bank_state.resources[ResourceType.WOOD] == 23
        assert sim.game_state.bank_state.resources[ResourceType.BRICK] == 9
