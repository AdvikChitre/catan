"""Board geometry - immutable topology"""
from typing import Dict, Set, Optional
from ..simulator.types.identifiers import TileId, VertexId, EdgeId, PortId, Coordinate


class VertexDefinition:
    """Immutable vertex topology"""
    def __init__(self, vertex_id: VertexId, coordinate: Coordinate):
        self.id = vertex_id
        self.coordinate = coordinate
        self.adjacent_vertex_ids: Set[VertexId] = set()
        self.adjacent_edge_ids: Set[EdgeId] = set()
        self.adjacent_tile_ids: Set[TileId] = set()
        self.port_id: Optional[PortId] = None


class EdgeDefinition:
    """Immutable edge topology"""
    def __init__(self, edge_id: EdgeId):
        self.id = edge_id
        self.vertex_ids: Set[VertexId] = set()


class TileDefinition:
    """Immutable tile topology"""
    def __init__(self, tile_id: TileId, coordinate: Coordinate):
        self.id = tile_id
        self.coordinate = coordinate
        self.vertex_ids: Set[VertexId] = set()
        self.edge_ids: Set[EdgeId] = set()


class PortDefinition:
    """Immutable port definition"""
    def __init__(self, port_id: PortId, port_type: str):
        self.id = port_id
        self.port_type = port_type
        self.vertex_ids: Set[VertexId] = set()


class BoardGeometry:
    """Immutable topology of the canonical Catan board"""
    def __init__(self):
        self.vertices: Dict[VertexId, VertexDefinition] = {}
        self.edges: Dict[EdgeId, EdgeDefinition] = {}
        self.tiles: Dict[TileId, TileDefinition] = {}
        self.ports: Dict[PortId, PortDefinition] = {}
