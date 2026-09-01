"""Player state"""
from typing import List, Dict
from ..simulator.types.resource import ResourceType
from ..simulator.types.identifiers import PlayerId


class PlayerState:
    """One player's state"""
    def __init__(self, player_id: PlayerId):
        self.player_id = player_id
        self.resources: Dict[ResourceType, int] = {
            ResourceType.WOOD: 0,
            ResourceType.BRICK: 0,
            ResourceType.SHEEP: 0,
            ResourceType.WHEAT: 0,
            ResourceType.ORE: 0,
        }
        self.development_cards: Dict[str, int] = {}
        self.victory_points: int = 0
        self.roads_remaining: int = 15
        self.settlements_remaining: int = 5
        self.cities_remaining: int = 4
