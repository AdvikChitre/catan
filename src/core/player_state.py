"""Player state"""
from typing import Dict, Set
from ..simulator.types.resource import ResourceType, DevelopmentCardType, ResourceCount, DevelopmentCardCount
from ..simulator.types.identifiers import PlayerId, EdgeId, VertexId


class PlayerState:
    """One player's state"""
    def __init__(self, player_id: PlayerId):
        self.player_id = player_id
        
        # Resources
        self.resources: ResourceCount = {
            ResourceType.WOOD: 0,
            ResourceType.BRICK: 0,
            ResourceType.SHEEP: 0,
            ResourceType.WHEAT: 0,
            ResourceType.ORE: 0,
        }
        
        # Development cards
        self.development_cards: DevelopmentCardCount = {
            DevelopmentCardType.KNIGHT: 0,
            DevelopmentCardType.ROAD_BUILDING: 0,
            DevelopmentCardType.YEAR_OF_PLENTY: 0,
            DevelopmentCardType.MONOPOLY: 0,
            DevelopmentCardType.VICTORY_POINT: 0,
        }
        
        # Played development cards (used this turn)
        self.played_development_cards: Set[DevelopmentCardType] = set()
        
        # Buildings and roads
        self.roads: Set[EdgeId] = set()
        self.settlements: Set[VertexId] = set()
        self.cities: Set[VertexId] = set()
        
        # Victory points (including development card points)
        self.victory_points: int = 0
        
        # Remaining resources to build with
        self.roads_remaining: int = 15
        self.settlements_remaining: int = 5
        self.cities_remaining: int = 4
        
        # Special achievements
        self.largest_army_count: int = 0  # Number of knights played
        self.has_largest_army: bool = False
        self.has_longest_road: bool = False

    def get_total_resources(self) -> int:
        """Get total number of resource cards held"""
        return sum(self.resources.values())

    def get_total_development_cards(self) -> int:
        """Get total number of unplayed development cards"""
        return sum(self.development_cards.values())

    def get_settlement_count(self) -> int:
        """Get total number of settlements"""
        return len(self.settlements)

    def get_city_count(self) -> int:
        """Get total number of cities"""
        return len(self.cities)

    def get_road_count(self) -> int:
        """Get total number of roads"""
        return len(self.roads)

    def get_calculated_victory_points(self) -> int:
        """Calculate victory points from settlements, cities, and dev cards"""
        points = 0
        points += self.get_settlement_count() * 1  # 1 point per settlement
        points += self.get_city_count() * 2  # 2 points per city
        points += self.development_cards[DevelopmentCardType.VICTORY_POINT]  # VP cards
        if self.has_largest_army:
            points += 2
        if self.has_longest_road:
            points += 2
        return points

    def __repr__(self):
        return (f"PlayerState({self.player_id.value}, "
                f"vp={self.victory_points}, "
                f"resources={sum(self.resources.values())}, "
                f"devs={sum(self.development_cards.values())})")
