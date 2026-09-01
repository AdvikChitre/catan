"""Domain identifiers"""
from enum import Enum
from typing import NewType


class PlayerId(Enum):
    """Player identifiers - exactly 4 players"""
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"
    P4 = "P4"


# Coordinate and ID types
TileId = NewType("TileId", str)
VertexId = NewType("VertexId", str)
EdgeId = NewType("EdgeId", str)
PortId = NewType("PortId", str)


class Coordinate:
    """2D coordinate for vertices"""
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if not isinstance(other, Coordinate):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __repr__(self):
        return f"Coordinate({self.x}, {self.y})"
