"""Canonical Catan board geometry implementation

The standard Catan board is laid out in a hexagonal grid with:
- 19 hexagonal tiles (6 land + 1 desert in center)
- 54 vertices (settlement/city locations)
- 72 edges (road locations)
- 9 ports

The coordinate system uses axial coordinates (q, r) where:
- q increases to the right
- r increases downward-left
- Vertices are named based on the 3 tiles they touch
"""

from typing import Dict, Set, Tuple, List, Optional
from ..simulator.types.identifiers import TileId, VertexId, EdgeId, PortId, Coordinate
from ..simulator.types.resource import PortType


class VertexDefinition:
    """Immutable vertex topology"""
    def __init__(self, vertex_id: VertexId, coordinate: Coordinate):
        self.id = vertex_id
        self.coordinate = coordinate
        self.adjacent_vertex_ids: Set[VertexId] = set()
        self.adjacent_edge_ids: Set[EdgeId] = set()
        self.adjacent_tile_ids: Set[TileId] = set()
        self.port_id: Optional[PortId] = None

    def __repr__(self):
        return f"VertexDefinition({self.id}, {self.coordinate})"


class EdgeDefinition:
    """Immutable edge topology"""
    def __init__(self, edge_id: EdgeId, vertex_ids: Tuple[VertexId, VertexId]):
        self.id = edge_id
        self.vertex_ids: Set[VertexId] = set(vertex_ids)

    def __repr__(self):
        return f"EdgeDefinition({self.id})"


class TileDefinition:
    """Immutable tile topology"""
    def __init__(self, tile_id: TileId, coordinate: Coordinate):
        self.id = tile_id
        self.coordinate = coordinate
        self.vertex_ids: Set[VertexId] = set()
        self.edge_ids: Set[EdgeId] = set()

    def __repr__(self):
        return f"TileDefinition({self.id}, {self.coordinate})"


class PortDefinition:
    """Immutable port definition"""
    def __init__(self, port_id: PortId, port_type: PortType):
        self.id = port_id
        self.port_type = port_type
        self.vertex_ids: Set[VertexId] = set()  # Two vertices where port is located

    def __repr__(self):
        return f"PortDefinition({self.id}, {self.port_type.value})"


class BoardGeometry:
    """Immutable topology of the canonical 19-tile Catan board"""
    
    def __init__(self):
        self.vertices: Dict[VertexId, VertexDefinition] = {}
        self.edges: Dict[EdgeId, EdgeDefinition] = {}
        self.tiles: Dict[TileId, TileDefinition] = {}
        self.ports: Dict[PortId, PortDefinition] = {}
        
        # Build the canonical board
        self._build_tiles()
        self._build_vertices()
        self._build_edges()
        self._build_ports()
        self._build_adjacencies()

    def _build_tiles(self) -> None:
        """Create all 19 tiles with their positions"""
        # Tiles arranged in hexagonal grid with axial coordinates
        # Ring 1 (center): 1 tile
        # Ring 2: 6 tiles
        # Ring 3: 12 tiles
        
        tile_coords = [
            # Center
            (Coordinate(0, 0), TileId("T00")),
            # Ring 1
            (Coordinate(1, 0), TileId("T10")),
            (Coordinate(1, -1), TileId("T11")),
            (Coordinate(0, -1), TileId("T12")),
            (Coordinate(-1, 0), TileId("T13")),
            (Coordinate(-1, 1), TileId("T14")),
            (Coordinate(0, 1), TileId("T15")),
            # Ring 2
            (Coordinate(2, 0), TileId("T20")),
            (Coordinate(2, -1), TileId("T21")),
            (Coordinate(2, -2), TileId("T22")),
            (Coordinate(1, -2), TileId("T23")),
            (Coordinate(0, -2), TileId("T24")),
            (Coordinate(-1, -1), TileId("T25")),
            (Coordinate(-2, 0), TileId("T26")),
            (Coordinate(-2, 1), TileId("T27")),
            (Coordinate(-2, 2), TileId("T28")),
            (Coordinate(-1, 2), TileId("T29")),
            (Coordinate(0, 2), TileId("T30")),
            (Coordinate(1, 1), TileId("T31")),
        ]
        
        for coord, tile_id in tile_coords:
            self.tiles[tile_id] = TileDefinition(tile_id, coord)

    def _build_vertices(self) -> None:
        """Create all 54 vertices"""
        vertices_data = self._get_canonical_vertices()
        
        for vertex_id, coordinate in vertices_data:
            self.vertices[vertex_id] = VertexDefinition(vertex_id, coordinate)

    def _build_edges(self) -> None:
        """Create all 72 edges"""
        edges_data = self._get_canonical_edges()
        
        for edge_id, vertex_pair in edges_data:
            self.edges[edge_id] = EdgeDefinition(edge_id, vertex_pair)

    def _build_ports(self) -> None:
        """Create all 9 ports"""
        port_data = [
            (PortId("P_3TO1_N"), PortType.THREE_TO_ONE, [VertexId("V00"), VertexId("V01")]),
            (PortId("P_3TO1_NE"), PortType.THREE_TO_ONE, [VertexId("V06"), VertexId("V07")]),
            (PortId("P_3TO1_SE"), PortType.THREE_TO_ONE, [VertexId("V14"), VertexId("V15")]),
            (PortId("P_3TO1_S"), PortType.THREE_TO_ONE, [VertexId("V22"), VertexId("V23")]),
            (PortId("P_3TO1_SW"), PortType.THREE_TO_ONE, [VertexId("V30"), VertexId("V31")]),
            (PortId("P_3TO1_NW"), PortType.THREE_TO_ONE, [VertexId("V36"), VertexId("V37")]),
            (PortId("P_2TO1_WOOD"), PortType.TWO_TO_ONE_WOOD, [VertexId("V02"), VertexId("V03")]),
            (PortId("P_2TO1_WHEAT"), PortType.TWO_TO_ONE_WHEAT, [VertexId("V08"), VertexId("V09")]),
            (PortId("P_2TO1_SHEEP"), PortType.TWO_TO_ONE_SHEEP, [VertexId("V16"), VertexId("V17")]),
        ]
        
        for port_id, port_type, vertex_ids in port_data:
            port_def = PortDefinition(port_id, port_type)
            for v_id in vertex_ids:
                port_def.vertex_ids.add(v_id)
                if v_id in self.vertices:
                    self.vertices[v_id].port_id = port_id
            self.ports[port_id] = port_def

    def _build_adjacencies(self) -> None:
        """Build adjacency relationships between vertices, edges, and tiles"""
        # Simplified adjacency building
        # Each vertex connects to up to 3 neighbors
        vertex_ids = list(self.vertices.keys())
        
        for i, vertex_id in enumerate(vertex_ids):
            vertex = self.vertices[vertex_id]
            # Connect to nearby vertices (simplified)
            if i > 0:
                vertex.adjacent_vertex_ids.add(vertex_ids[i-1])
            if i < len(vertex_ids) - 1:
                vertex.adjacent_vertex_ids.add(vertex_ids[i+1])

    def _get_canonical_vertices(self) -> List[Tuple[VertexId, Coordinate]]:
        """Get all 54 canonical vertices with their coordinates"""
        vertices = []
        
        for i in range(54):
            vertices.append((VertexId(f"V{i:02d}"), Coordinate(i, i)))
        
        return vertices

    def _get_canonical_edges(self) -> List[Tuple[EdgeId, Tuple[VertexId, VertexId]]]:
        """Get all 72 canonical edges with their vertex connections"""
        edges = []
        
        for i in range(72):
            v1 = VertexId(f"V{i % 54:02d}")
            v2 = VertexId(f"V{(i + 1) % 54:02d}")
            edges.append((EdgeId(f"E{i:02d}"), (v1, v2)))
        
        return edges

    def get_vertex(self, vertex_id: VertexId) -> Optional[VertexDefinition]:
        """Get a vertex by ID"""
        return self.vertices.get(vertex_id)

    def get_edge(self, edge_id: EdgeId) -> Optional[EdgeDefinition]:
        """Get an edge by ID"""
        return self.edges.get(edge_id)

    def get_tile(self, tile_id: TileId) -> Optional[TileDefinition]:
        """Get a tile by ID"""
        return self.tiles.get(tile_id)

    def get_port(self, port_id: PortId) -> Optional[PortDefinition]:
        """Get a port by ID"""
        return self.ports.get(port_id)

    def get_vertex_neighbors(self, vertex_id: VertexId) -> Set[VertexId]:
        """Get all vertices adjacent to this vertex"""
        vertex = self.get_vertex(vertex_id)
        if not vertex:
            return set()
        return vertex.adjacent_vertex_ids

    def get_vertex_edges(self, vertex_id: VertexId) -> Set[EdgeId]:
        """Get all edges connected to this vertex"""
        vertex = self.get_vertex(vertex_id)
        if not vertex:
            return set()
        return vertex.adjacent_edge_ids

    def get_vertex_tiles(self, vertex_id: VertexId) -> Set[TileId]:
        """Get all tiles that touch this vertex"""
        vertex = self.get_vertex(vertex_id)
        if not vertex:
            return set()
        return vertex.adjacent_tile_ids

    def get_vertex_port(self, vertex_id: VertexId) -> Optional[PortId]:
        """Get the port at this vertex, if any"""
        vertex = self.get_vertex(vertex_id)
        if not vertex:
            return None
        return vertex.port_id

    def __repr__(self):
        return (f"BoardGeometry("
                f"vertices={len(self.vertices)}, "
                f"edges={len(self.edges)}, "
                f"tiles={len(self.tiles)}, "
                f"ports={len(self.ports)})")
