from typing import List
from tile import Tile
from port import Port
from simulator.types.resource import Resource

#       (05)(15)(25)(35)(45)(55)(65)
#   (04)(14)(24)(34)(44)(54)(64)(74)(84)
#(03)(13)(23)(33)(43)(53)(63)(73)(83)(93)(103)
#(02)(12)(22)(32)(42)(52)(62)(72)(82)(92)(102)
#   (01)(11)(21)(31)(41)(51)(61)(71)(81)
#       (00)(10)(20)(30)(40)(50)(60)
class Board:
    def __init__(self):
        self.nodes = []
        self.ports = self.ports = {
            (0, 0): Resource.SHEEP,
            (1, 0): Resource.SHEEP,

            (0, 1): None,
            (1, 2): None,

            (0, 3): Resource.WOOD,
            (1, 3): Resource.WOOD,

            (0, 5): None,
            (1, 5): None,

            (3, 5): Resource.BRICK,
            (4, 5): Resource.BRICK,

            (6, 5): None,
            (7, 4): None,

            (10, 3): Resource.HAY,
            (10, 2): Resource.HAY,

            (8, 1): None,
            (7, 1): None,

            (5, 0): Resource.ORE,
            (4, 0): Resource.ORE,
        }
        


class Node:
    def __init__(self, coords: List[int], tiles: List[Tile], port : Port ):
        self.coords = coords 
        self.tiles = tiles # 3 surrounding tiles
        self.port = port 