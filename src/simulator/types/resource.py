"""Resource types and constants"""
from enum import Enum
from typing import Dict


class ResourceType(Enum):
    """Standard Catan resource types"""
    WOOD = "WOOD"
    BRICK = "BRICK"
    SHEEP = "SHEEP"
    WHEAT = "WHEAT"
    ORE = "ORE"

    @staticmethod
    def tradeable_resources() -> list:
        """Get all tradeable resources (all resources)"""
        return [ResourceType.WOOD, ResourceType.BRICK, ResourceType.SHEEP, 
                ResourceType.WHEAT, ResourceType.ORE]


class DevelopmentCardType(Enum):
    """Development card types"""
    KNIGHT = "KNIGHT"
    ROAD_BUILDING = "ROAD_BUILDING"
    YEAR_OF_PLENTY = "YEAR_OF_PLENTY"
    MONOPOLY = "MONOPOLY"
    VICTORY_POINT = "VICTORY_POINT"


class PortType(Enum):
    """Port exchange rates"""
    THREE_TO_ONE = "THREE_TO_ONE"  # 3 of any resource for 1 of any
    TWO_TO_ONE_WOOD = "TWO_TO_ONE_WOOD"
    TWO_TO_ONE_BRICK = "TWO_TO_ONE_BRICK"
    TWO_TO_ONE_SHEEP = "TWO_TO_ONE_SHEEP"
    TWO_TO_ONE_WHEAT = "TWO_TO_ONE_WHEAT"
    TWO_TO_ONE_ORE = "TWO_TO_ONE_ORE"

    def get_resource_type(self) -> 'ResourceType':
        """Get the resource type for 2:1 ports, or None for 3:1"""
        mapping = {
            PortType.TWO_TO_ONE_WOOD: ResourceType.WOOD,
            PortType.TWO_TO_ONE_BRICK: ResourceType.BRICK,
            PortType.TWO_TO_ONE_SHEEP: ResourceType.SHEEP,
            PortType.TWO_TO_ONE_WHEAT: ResourceType.WHEAT,
            PortType.TWO_TO_ONE_ORE: ResourceType.ORE,
        }
        return mapping.get(self)

    def is_two_to_one(self) -> bool:
        """Check if this is a 2:1 port"""
        return self != PortType.THREE_TO_ONE


# Resource count type (maps resources to quantities)
ResourceCount = Dict[ResourceType, int]
DevelopmentCardCount = Dict[DevelopmentCardType, int]