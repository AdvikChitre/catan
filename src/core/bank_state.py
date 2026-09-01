"""Bank state - resource pool and development cards"""
from typing import Dict
from ..simulator.types.resource import ResourceType


class BankState:
    """Bank resource pool and development card deck"""
    def __init__(self):
        self.resources: Dict[ResourceType, int] = {
            ResourceType.WOOD: 19,
            ResourceType.BRICK: 19,
            ResourceType.SHEEP: 19,
            ResourceType.WHEAT: 19,
            ResourceType.ORE: 19,
        }
        self.development_cards: Dict[str, int] = {
            "KNIGHT": 14,
            "ROAD_BUILDING": 2,
            "YEAR_OF_PLENTY": 2,
            "MONOPOLY": 2,
            "VICTORY_POINT": 5,
        }
