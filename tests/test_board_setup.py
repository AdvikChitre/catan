"""Board setup and deterministic randomization tests."""

from src.board import BoardGeometry, BoardSetup
from src.core import GameState
from src.core.player_state import PlayerState
from src.simulation.seeded_rng import SeededRng
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import ResourceType, DevelopmentCardType
from src.views import GameViewBuilder


class TestBoardSetup:
    def test_board_setup_assigns_standard_resource_distribution(self):
        board = BoardGeometry()
        rng = SeededRng(1234)
        board_state = BoardSetup.build_board_state(board, rng)

        counts = {resource: 0 for resource in ResourceType}
        for tile in board_state.tiles.values():
            if tile.resource_type is not None:
                counts[tile.resource_type] += 1

        assert counts == {
            ResourceType.WOOD: 4,
            ResourceType.BRICK: 3,
            ResourceType.SHEEP: 4,
            ResourceType.WHEAT: 4,
            ResourceType.ORE: 3,
        }
        assert sum(1 for tile in board_state.tiles.values() if tile.resource_type is None) == 1

    def test_board_setup_assigns_all_standard_number_tokens(self):
        board = BoardGeometry()
        rng = SeededRng(11)
        board_state = BoardSetup.build_board_state(board, rng)

        tokens = [tile.number_token for tile in board_state.tiles.values() if tile.number_token is not None]
        assert sorted(tokens) == [2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12]
        assert any(tile.has_robber for tile in board_state.tiles.values() if tile.resource_type is None)
        assert board_state.robber_tile_id is not None

    def test_board_setup_is_reproducible_for_same_seed(self):
        board = BoardGeometry()
        first = BoardSetup.build_board_state(board, SeededRng(99))
        second = BoardSetup.build_board_state(board, SeededRng(99))

        first_tiles = {tile_id: (tile.resource_type, tile.number_token, tile.has_robber) for tile_id, tile in first.tiles.items()}
        second_tiles = {tile_id: (tile.resource_type, tile.number_token, tile.has_robber) for tile_id, tile in second.tiles.items()}

        assert first_tiles == second_tiles
        assert first.robber_tile_id == second.robber_tile_id

    def test_development_deck_is_shuffled_but_preserves_counts(self):
        deck = BoardSetup.shuffle_development_deck(SeededRng(5))
        counts = {card: 0 for card in DevelopmentCardType}
        for card in deck:
            counts[card] += 1

        assert counts == {
            DevelopmentCardType.KNIGHT: 14,
            DevelopmentCardType.ROAD_BUILDING: 2,
            DevelopmentCardType.YEAR_OF_PLENTY: 2,
            DevelopmentCardType.MONOPOLY: 2,
            DevelopmentCardType.VICTORY_POINT: 5,
        }


class TestGameViewBuilder:
    def test_game_view_builder_builds_player_specific_snapshot(self):
        game = GameState()
        game.game_id = "G-42"
        game.players = [PlayerState(PlayerId.P1), PlayerState(PlayerId.P2)]
        game.players[0].resources[ResourceType.WOOD] = 3
        game.players[1].resources[ResourceType.ORE] = 2
        game.players[1].development_cards[DevelopmentCardType.KNIGHT] = 1

        game.board_state = BoardSetup.build_board_state(BoardGeometry(), SeededRng(1))
        game.turn_state = type("TurnState", (), {"turn_number": 3, "current_player": PlayerId.P1})()
        game.phase = type("Phase", (), {"value": "NORMAL_PLAY"})()

        view = GameViewBuilder(game).build_view(PlayerId.P1)

        assert view.game_id == "G-42"
        assert view.self.player_id == PlayerId.P1
        assert view.self.resources[ResourceType.WOOD] == 3
        assert len(view.opponents) == 1
        assert view.opponents[0].player_id == PlayerId.P2
        assert view.opponents[0].resources == {}
        assert len(view.board.tiles) == 19
        assert view.turn.current_player == PlayerId.P1

    def test_game_view_hides_private_opponent_information(self):
        game = GameState()
        game.players = [PlayerState(PlayerId.P1), PlayerState(PlayerId.P2)]
        game.players[1].resources[ResourceType.WHEAT] = 5
        game.players[1].development_cards[DevelopmentCardType.VICTORY_POINT] = 2
        game.board_state = BoardSetup.build_board_state(BoardGeometry(), SeededRng(7))
        game.turn_state = type("TurnState", (), {"turn_number": 1, "current_player": PlayerId.P1})()
        game.phase = type("Phase", (), {"value": "SETUP_FIRST"})()

        view = GameViewBuilder(game).build_view(PlayerId.P1)

        opp = view.opponents[0]
        assert opp.resources == {}
        assert opp.development_cards == {}
        assert "WHEAT" not in str(opp.resources)
