"""Unit tests for domain types"""
import pytest
from src.simulator.types.resource import ResourceType, DevelopmentCardType, PortType
from src.simulator.types.identifiers import PlayerId, Coordinate, BuildingType
from src.core.building import Building, Road, VertexState, EdgeState, TileState
from src.core.player_state import PlayerState
from src.core.bank_state import BankState
from src.core.board_state import BoardState
from src.core.turn_state import TurnState
from src.core.game_state import GameState, GamePhase, GameStatus


class TestResourceTypes:
    """Test ResourceType enum"""

    def test_all_resources_present(self):
        """Test all five resources are defined"""
        assert ResourceType.WOOD in ResourceType.__members__.values()
        assert ResourceType.BRICK in ResourceType.__members__.values()
        assert ResourceType.SHEEP in ResourceType.__members__.values()
        assert ResourceType.WHEAT in ResourceType.__members__.values()
        assert ResourceType.ORE in ResourceType.__members__.values()

    def test_tradeable_resources(self):
        """Test tradeable resources list"""
        tradeable = ResourceType.tradeable_resources()
        assert len(tradeable) == 5
        assert all(isinstance(r, ResourceType) for r in tradeable)


class TestDevelopmentCardTypes:
    """Test DevelopmentCardType enum"""

    def test_all_card_types_present(self):
        """Test all card types are defined"""
        assert DevelopmentCardType.KNIGHT in DevelopmentCardType.__members__.values()
        assert DevelopmentCardType.ROAD_BUILDING in DevelopmentCardType.__members__.values()
        assert DevelopmentCardType.YEAR_OF_PLENTY in DevelopmentCardType.__members__.values()
        assert DevelopmentCardType.MONOPOLY in DevelopmentCardType.__members__.values()
        assert DevelopmentCardType.VICTORY_POINT in DevelopmentCardType.__members__.values()

    def test_card_count(self):
        """Test correct number of card types"""
        assert len(DevelopmentCardType.__members__) == 5


class TestPortTypes:
    """Test PortType enum"""

    def test_three_to_one_port(self):
        """Test 3:1 port"""
        port = PortType.THREE_TO_ONE
        assert not port.is_two_to_one()
        assert port.get_resource_type() is None

    def test_two_to_one_ports(self):
        """Test 2:1 ports"""
        assert PortType.TWO_TO_ONE_WOOD.is_two_to_one()
        assert PortType.TWO_TO_ONE_WOOD.get_resource_type() == ResourceType.WOOD

        assert PortType.TWO_TO_ONE_BRICK.is_two_to_one()
        assert PortType.TWO_TO_ONE_BRICK.get_resource_type() == ResourceType.BRICK

        assert PortType.TWO_TO_ONE_SHEEP.is_two_to_one()
        assert PortType.TWO_TO_ONE_SHEEP.get_resource_type() == ResourceType.SHEEP

        assert PortType.TWO_TO_ONE_WHEAT.is_two_to_one()
        assert PortType.TWO_TO_ONE_WHEAT.get_resource_type() == ResourceType.WHEAT

        assert PortType.TWO_TO_ONE_ORE.is_two_to_one()
        assert PortType.TWO_TO_ONE_ORE.get_resource_type() == ResourceType.ORE


class TestPlayerId:
    """Test PlayerId enum"""

    def test_four_players(self):
        """Test exactly four players defined"""
        players = PlayerId.all_players()
        assert len(players) == 4
        assert PlayerId.P1 in players
        assert PlayerId.P2 in players
        assert PlayerId.P3 in players
        assert PlayerId.P4 in players

    def test_player_values(self):
        """Test player string values"""
        assert PlayerId.P1.value == "P1"
        assert PlayerId.P2.value == "P2"
        assert PlayerId.P3.value == "P3"
        assert PlayerId.P4.value == "P4"


class TestCoordinate:
    """Test Coordinate class"""

    def test_coordinate_creation(self):
        """Test creating coordinates"""
        coord = Coordinate(5, 10)
        assert coord.x == 5
        assert coord.y == 10

    def test_coordinate_equality(self):
        """Test coordinate equality"""
        coord1 = Coordinate(5, 10)
        coord2 = Coordinate(5, 10)
        coord3 = Coordinate(5, 11)
        assert coord1 == coord2
        assert coord1 != coord3

    def test_coordinate_hash(self):
        """Test coordinates are hashable"""
        coord1 = Coordinate(5, 10)
        coord2 = Coordinate(5, 10)
        coord_set = {coord1, coord2}
        assert len(coord_set) == 1  # Should be same hash

    def test_coordinate_sorting(self):
        """Test coordinates can be sorted"""
        coords = [Coordinate(5, 10), Coordinate(3, 5), Coordinate(5, 5)]
        sorted_coords = sorted(coords)
        assert sorted_coords[0].x == 3
        assert sorted_coords[1] == Coordinate(5, 5)
        assert sorted_coords[2] == Coordinate(5, 10)


class TestBuilding:
    """Test Building class"""

    def test_empty_building(self):
        """Test creating empty building"""
        building = Building.empty()
        assert building.is_empty()
        assert building.get_victory_points() == 0

    def test_settlement(self):
        """Test creating settlement"""
        building = Building.settlement(PlayerId.P1)
        assert not building.is_empty()
        assert building.type == BuildingType.SETTLEMENT
        assert building.owner == PlayerId.P1
        assert building.get_victory_points() == 1

    def test_city(self):
        """Test creating city"""
        building = Building.city(PlayerId.P1)
        assert not building.is_empty()
        assert building.type == BuildingType.CITY
        assert building.owner == PlayerId.P1
        assert building.get_victory_points() == 2

    def test_building_upgrade(self):
        """Test upgrading settlement to city"""
        settlement = Building.settlement(PlayerId.P1)
        city = Building.city(PlayerId.P1)
        assert settlement.get_victory_points() == 1
        assert city.get_victory_points() == 2


class TestRoad:
    """Test Road class"""

    def test_empty_road(self):
        """Test empty road"""
        road = Road.empty()
        assert road.is_empty()
        assert road.owner is None

    def test_owned_road(self):
        """Test owned road"""
        road = Road(PlayerId.P2)
        assert not road.is_empty()
        assert road.owner == PlayerId.P2


class TestPlayerState:
    """Test PlayerState class"""

    def test_player_creation(self):
        """Test creating player state"""
        player = PlayerState(PlayerId.P1)
        assert player.player_id == PlayerId.P1
        assert player.get_total_resources() == 0
        assert player.get_total_development_cards() == 0

    def test_initial_resources(self):
        """Test initial resources are zero"""
        player = PlayerState(PlayerId.P1)
        for resource in ResourceType.tradeable_resources():
            assert player.resources[resource] == 0

    def test_initial_buildings(self):
        """Test initial building counts"""
        player = PlayerState(PlayerId.P1)
        assert player.get_settlement_count() == 0
        assert player.get_city_count() == 0
        assert player.get_road_count() == 0

    def test_total_resources(self):
        """Test total resources calculation"""
        player = PlayerState(PlayerId.P1)
        player.resources[ResourceType.WOOD] = 3
        player.resources[ResourceType.BRICK] = 2
        assert player.get_total_resources() == 5

    def test_total_development_cards(self):
        """Test total development cards calculation"""
        player = PlayerState(PlayerId.P1)
        player.development_cards[DevelopmentCardType.KNIGHT] = 2
        player.development_cards[DevelopmentCardType.ROAD_BUILDING] = 1
        assert player.get_total_development_cards() == 3

    def test_calculated_victory_points(self):
        """Test victory points calculation"""
        player = PlayerState(PlayerId.P1)
        player.settlements.add("vertex_1")
        player.settlements.add("vertex_2")
        player.cities.add("vertex_3")
        player.development_cards[DevelopmentCardType.VICTORY_POINT] = 1
        
        vp = player.get_calculated_victory_points()
        # 2 settlements (2 points) + 1 city (2 points) + 1 VP card = 5 points
        assert vp == 5

    def test_victory_points_with_largest_army(self):
        """Test victory points with largest army"""
        player = PlayerState(PlayerId.P1)
        player.has_largest_army = True
        assert player.get_calculated_victory_points() == 2

    def test_victory_points_with_longest_road(self):
        """Test victory points with longest road"""
        player = PlayerState(PlayerId.P1)
        player.has_longest_road = True
        assert player.get_calculated_victory_points() == 2


class TestBankState:
    """Test BankState class"""

    def test_initial_resources(self):
        """Test bank starts with correct resources"""
        bank = BankState()
        assert bank.get_total_resources() == 95  # 19 * 5 resources
        for resource in ResourceType.tradeable_resources():
            assert bank.resources[resource] == 19

    def test_initial_development_cards(self):
        """Test bank starts with correct development cards"""
        bank = BankState()
        assert bank.get_total_development_cards() == 25
        assert bank.development_cards[DevelopmentCardType.KNIGHT] == 14
        assert bank.development_cards[DevelopmentCardType.ROAD_BUILDING] == 2
        assert bank.development_cards[DevelopmentCardType.YEAR_OF_PLENTY] == 2
        assert bank.development_cards[DevelopmentCardType.MONOPOLY] == 2
        assert bank.development_cards[DevelopmentCardType.VICTORY_POINT] == 5

    def test_has_resource(self):
        """Test resource availability checks"""
        bank = BankState()
        assert bank.has_resource(ResourceType.WOOD, 19)
        assert not bank.has_resource(ResourceType.WOOD, 20)
        bank.resources[ResourceType.WOOD] = 0
        assert not bank.has_resource(ResourceType.WOOD, 1)

    def test_has_development_card(self):
        """Test development card availability"""
        bank = BankState()
        assert bank.has_development_card(DevelopmentCardType.KNIGHT)
        bank.development_cards[DevelopmentCardType.KNIGHT] = 0
        assert not bank.has_development_card(DevelopmentCardType.KNIGHT)


class TestBoardState:
    """Test BoardState class"""

    def test_board_creation(self):
        """Test creating board state"""
        board = BoardState()
        assert len(board.tiles) == 0
        assert len(board.vertices) == 0
        assert len(board.edges) == 0
        assert board.robber_tile_id is None


class TestTurnState:
    """Test TurnState class"""

    def test_turn_creation(self):
        """Test creating turn state"""
        turn = TurnState()
        assert turn.current_player is None
        assert turn.turn_number == 0
        assert turn.dice_roll is None
        assert turn.is_pre_roll()

    def test_phase_checks(self):
        """Test phase checking methods"""
        turn = TurnState()
        assert turn.is_pre_roll()
        assert not turn.is_rolled()
        assert not turn.is_playing()

        turn.phase = "ROLLED"
        assert not turn.is_pre_roll()
        assert turn.is_rolled()
        assert not turn.is_playing()

        turn.phase = "PLAYING"
        assert not turn.is_pre_roll()
        assert not turn.is_rolled()
        assert turn.is_playing()


class TestGameState:
    """Test GameState class"""

    def test_game_creation(self):
        """Test creating game state"""
        game = GameState()
        assert game.game_id == ""
        assert game.seed == 0
        assert game.phase == GamePhase.SETUP_FIRST
        assert game.status == GameStatus.ACTIVE
        assert len(game.players) == 0

    def test_phase_checks(self):
        """Test phase checking methods"""
        game = GameState()
        assert game.is_setup_phase()
        assert not game.is_normal_play_phase()
        assert not game.is_game_over()

        game.phase = GamePhase.NORMAL_PLAY
        assert not game.is_setup_phase()
        assert game.is_normal_play_phase()
        assert not game.is_game_over()

        game.status = GameStatus.COMPLETED
        assert game.is_game_over()

    def test_game_status_values(self):
        """Test game status values"""
        assert GameStatus.ACTIVE.value == "ACTIVE"
        assert GameStatus.COMPLETED.value == "COMPLETED"
        assert GameStatus.ERROR.value == "ERROR"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
