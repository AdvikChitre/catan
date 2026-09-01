"""Building state types"""
from typing import Optional, Union
from ..simulator.types.identifiers import PlayerId, BuildingType


class Building:
    """Represents a building at a vertex"""
    def __init__(self, building_type: Optional[BuildingType] = None, 
                 owner: Optional[PlayerId] = None):
        self.type = building_type
        self.owner = owner

    @staticmethod
    def empty():
        """Create an empty building"""
        return Building(None, None)

    @staticmethod
    def settlement(owner: PlayerId):
        """Create a settlement"""
        return Building(BuildingType.SETTLEMENT, owner)

    @staticmethod
    def city(owner: PlayerId):
        """Create a city"""
        return Building(BuildingType.CITY, owner)

    def is_empty(self) -> bool:
        """Check if vertex is empty"""
        return self.type is None

    def get_victory_points(self) -> int:
        """Get victory points this building provides"""
        if self.type == BuildingType.SETTLEMENT:
            return 1
        elif self.type == BuildingType.CITY:
            return 2
        return 0

    def __repr__(self):
        if self.type is None:
            return "Building(EMPTY)"
        return f"Building({self.type.value}, {self.owner.value if self.owner else 'None'})"


class Road:
    """Represents a road on an edge"""
    def __init__(self, owner: Optional[PlayerId] = None):
        self.owner = owner

    @staticmethod
    def empty():
        """Create an empty road"""
        return Road(None)

    def is_empty(self) -> bool:
        """Check if edge is empty"""
        return self.owner is None

    def __repr__(self):
        return f"Road({self.owner.value if self.owner else 'EMPTY'})"


class VertexState:
    """State of a vertex (building location)"""
    def __init__(self, vertex_id: str, building: Optional[Building] = None):
        self.vertex_id = vertex_id
        self.building = building if building is not None else Building.empty()

    def __repr__(self):
        return f"VertexState({self.vertex_id}, {self.building})"


class EdgeState:
    """State of an edge (road location)"""
    def __init__(self, edge_id: str, road: Optional[Road] = None):
        self.edge_id = edge_id
        self.road = road if road is not None else Road.empty()

    def __repr__(self):
        return f"EdgeState({self.edge_id}, {self.road})"


class TileState:
    """State of a tile"""
    def __init__(self, tile_id: str, resource_type: 'ResourceType', 
                 number_token: Optional[int] = None, has_robber: bool = False):
        self.tile_id = tile_id
        self.resource_type = resource_type
        self.number_token = number_token  # None for desert
        self.has_robber = has_robber

    def __repr__(self):
        return f"TileState({self.tile_id}, {self.resource_type.value}, number={self.number_token}, robber={self.has_robber})"
