"""Board state - mutable gameplay state"""
from typing import Dict, Optional
from ..simulator.types.identifiers import TileId, VertexId, EdgeId


class BoardState:
    """Mutable board information: tiles, robber, buildings, roads"""
    def __init__(self):
        self.tiles: Dict[TileId, 'TileState'] = {}
        self.vertices: Dict[VertexId, 'VertexState'] = {}
        self.edges: Dict[EdgeId, 'EdgeState'] = {}
        self.robber_tile_id: Optional[TileId] = None
