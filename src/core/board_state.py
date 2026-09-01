"""Board state - mutable gameplay state"""
from typing import Dict, Optional
from ..simulator.types.identifiers import TileId, VertexId, EdgeId
from .building import VertexState, EdgeState, TileState


class BoardState:
    """Mutable board information: tiles, robber, buildings, roads"""
    def __init__(self):
        self.tiles: Dict[TileId, TileState] = {}
        self.vertices: Dict[VertexId, VertexState] = {}
        self.edges: Dict[EdgeId, EdgeState] = {}
        self.robber_tile_id: Optional[TileId] = None

    def get_tile(self, tile_id: TileId) -> Optional[TileState]:
        """Get a tile by ID"""
        return self.tiles.get(tile_id)

    def get_vertex(self, vertex_id: VertexId) -> Optional[VertexState]:
        """Get a vertex by ID"""
        return self.vertices.get(vertex_id)

    def get_edge(self, edge_id: EdgeId) -> Optional[EdgeState]:
        """Get an edge by ID"""
        return self.edges.get(edge_id)
