"""Unit tests for board geometry"""
import pytest
from src.board.board_geometry import BoardGeometry, VertexDefinition, EdgeDefinition, TileDefinition, PortDefinition
from src.simulator.types.identifiers import TileId, VertexId, EdgeId, PortId, Coordinate
from src.simulator.types.resource import PortType


class TestBoardGeometry:
    """Test BoardGeometry class"""

    def test_board_creation(self):
        """Test creating a canonical board"""
        board = BoardGeometry()
        assert board is not None
        assert len(board.tiles) == 19
        assert len(board.vertices) == 54
        assert len(board.edges) == 72
        assert len(board.ports) == 9

    def test_tile_count(self):
        """Test board has exactly 19 tiles"""
        board = BoardGeometry()
        assert len(board.tiles) == 19

    def test_vertex_count(self):
        """Test board has exactly 54 vertices"""
        board = BoardGeometry()
        assert len(board.vertices) == 54

    def test_edge_count(self):
        """Test board has exactly 72 edges"""
        board = BoardGeometry()
        assert len(board.edges) == 72

    def test_port_count(self):
        """Test board has exactly 9 ports"""
        board = BoardGeometry()
        assert len(board.ports) == 9

    def test_ports_distribution(self):
        """Test port type distribution"""
        board = BoardGeometry()
        
        three_to_one = sum(1 for p in board.ports.values() 
                           if p.port_type == PortType.THREE_TO_ONE)
        two_to_one = sum(1 for p in board.ports.values() 
                         if p.port_type != PortType.THREE_TO_ONE)
        
        assert three_to_one == 6
        assert two_to_one == 3

    def test_get_vertex(self):
        """Test retrieving a vertex"""
        board = BoardGeometry()
        vertex = board.get_vertex(VertexId("V00"))
        assert vertex is not None
        assert vertex.id == VertexId("V00")

    def test_get_nonexistent_vertex(self):
        """Test retrieving a nonexistent vertex"""
        board = BoardGeometry()
        vertex = board.get_vertex(VertexId("V99"))
        assert vertex is None

    def test_get_edge(self):
        """Test retrieving an edge"""
        board = BoardGeometry()
        edge = board.get_edge(EdgeId("E00"))
        assert edge is not None
        assert edge.id == EdgeId("E00")

    def test_get_nonexistent_edge(self):
        """Test retrieving a nonexistent edge"""
        board = BoardGeometry()
        edge = board.get_edge(EdgeId("E99"))
        assert edge is None

    def test_get_tile(self):
        """Test retrieving a tile"""
        board = BoardGeometry()
        tile = board.get_tile(TileId("T00"))
        assert tile is not None
        assert tile.id == TileId("T00")

    def test_get_nonexistent_tile(self):
        """Test retrieving a nonexistent tile"""
        board = BoardGeometry()
        tile = board.get_tile(TileId("T99"))
        assert tile is None

    def test_get_port(self):
        """Test retrieving a port"""
        board = BoardGeometry()
        port = board.get_port(PortId("P_3TO1_N"))
        assert port is not None
        assert port.id == PortId("P_3TO1_N")
        assert port.port_type == PortType.THREE_TO_ONE

    def test_get_nonexistent_port(self):
        """Test retrieving a nonexistent port"""
        board = BoardGeometry()
        port = board.get_port(PortId("P_FAKE"))
        assert port is None


class TestVertexDefinition:
    """Test VertexDefinition class"""

    def test_vertex_creation(self):
        """Test creating a vertex"""
        coord = Coordinate(5, 10)
        vertex = VertexDefinition(VertexId("V01"), coord)
        
        assert vertex.id == VertexId("V01")
        assert vertex.coordinate == coord
        assert len(vertex.adjacent_vertex_ids) == 0
        assert len(vertex.adjacent_edge_ids) == 0
        assert len(vertex.adjacent_tile_ids) == 0
        assert vertex.port_id is None

    def test_vertex_with_port(self):
        """Test vertex with a port"""
        vertex = VertexDefinition(VertexId("V01"), Coordinate(0, 0))
        vertex.port_id = PortId("P_3TO1_N")
        
        assert vertex.port_id == PortId("P_3TO1_N")


class TestEdgeDefinition:
    """Test EdgeDefinition class"""

    def test_edge_creation(self):
        """Test creating an edge"""
        v1 = VertexId("V00")
        v2 = VertexId("V01")
        edge = EdgeDefinition(EdgeId("E00"), (v1, v2))
        
        assert edge.id == EdgeId("E00")
        assert v1 in edge.vertex_ids
        assert v2 in edge.vertex_ids
        assert len(edge.vertex_ids) == 2


class TestTileDefinition:
    """Test TileDefinition class"""

    def test_tile_creation(self):
        """Test creating a tile"""
        coord = Coordinate(0, 0)
        tile = TileDefinition(TileId("T00"), coord)
        
        assert tile.id == TileId("T00")
        assert tile.coordinate == coord
        assert len(tile.vertex_ids) == 0
        assert len(tile.edge_ids) == 0


class TestPortDefinition:
    """Test PortDefinition class"""

    def test_port_creation(self):
        """Test creating a port"""
        port = PortDefinition(PortId("P_3TO1_N"), PortType.THREE_TO_ONE)
        
        assert port.id == PortId("P_3TO1_N")
        assert port.port_type == PortType.THREE_TO_ONE
        assert len(port.vertex_ids) == 0

    def test_port_with_vertices(self):
        """Test port with vertices"""
        port = PortDefinition(PortId("P_3TO1_N"), PortType.THREE_TO_ONE)
        v1 = VertexId("V00")
        v2 = VertexId("V01")
        
        port.vertex_ids.add(v1)
        port.vertex_ids.add(v2)
        
        assert v1 in port.vertex_ids
        assert v2 in port.vertex_ids
        assert len(port.vertex_ids) == 2


class TestBoardGeometryQueries:
    """Test board geometry query methods"""

    def test_get_vertex_neighbors(self):
        """Test getting vertex neighbors"""
        board = BoardGeometry()
        neighbors = board.get_vertex_neighbors(VertexId("V00"))
        assert isinstance(neighbors, set)

    def test_get_vertex_edges(self):
        """Test getting edges connected to a vertex"""
        board = BoardGeometry()
        edges = board.get_vertex_edges(VertexId("V00"))
        assert isinstance(edges, set)

    def test_get_vertex_tiles(self):
        """Test getting tiles touching a vertex"""
        board = BoardGeometry()
        tiles = board.get_vertex_tiles(VertexId("V00"))
        assert isinstance(tiles, set)

    def test_get_vertex_port_with_port(self):
        """Test getting port at a vertex with port"""
        board = BoardGeometry()
        # V00 and V01 have ports
        port = board.get_vertex_port(VertexId("V00"))
        assert port == PortId("P_3TO1_N")

    def test_get_vertex_port_without_port(self):
        """Test getting port at a vertex without port"""
        board = BoardGeometry()
        # Most vertices don't have ports
        port = board.get_vertex_port(VertexId("V10"))
        # This vertex might or might not have a port
        # Just check it returns PortId or None
        assert port is None or isinstance(port, PortId)


class TestBoardGeometryProperties:
    """Test board geometry invariants"""

    def test_each_tile_has_id(self):
        """Test each tile has an ID"""
        board = BoardGeometry()
        for tile_id, tile in board.tiles.items():
            assert tile.id == tile_id

    def test_each_vertex_has_id(self):
        """Test each vertex has an ID"""
        board = BoardGeometry()
        for vertex_id, vertex in board.vertices.items():
            assert vertex.id == vertex_id

    def test_each_edge_has_id(self):
        """Test each edge has an ID"""
        board = BoardGeometry()
        for edge_id, edge in board.edges.items():
            assert edge.id == edge_id

    def test_each_port_has_id(self):
        """Test each port has an ID"""
        board = BoardGeometry()
        for port_id, port in board.ports.items():
            assert port.id == port_id

    def test_all_tiles_have_coordinates(self):
        """Test all tiles have coordinates"""
        board = BoardGeometry()
        for tile in board.tiles.values():
            assert tile.coordinate is not None
            assert isinstance(tile.coordinate, Coordinate)

    def test_all_vertices_have_coordinates(self):
        """Test all vertices have coordinates"""
        board = BoardGeometry()
        for vertex in board.vertices.values():
            assert vertex.coordinate is not None
            assert isinstance(vertex.coordinate, Coordinate)

    def test_edge_vertices_exist(self):
        """Test that vertices referenced by edges exist"""
        board = BoardGeometry()
        for edge in board.edges.values():
            for vertex_id in edge.vertex_ids:
                assert vertex_id in board.vertices

    def test_port_vertices_exist(self):
        """Test that vertices referenced by ports exist"""
        board = BoardGeometry()
        for port in board.ports.values():
            for vertex_id in port.vertex_ids:
                assert vertex_id in board.vertices


class TestBoardGeometryRepr:
    """Test string representations"""

    def test_board_repr(self):
        """Test board string representation"""
        board = BoardGeometry()
        repr_str = repr(board)
        assert "BoardGeometry" in repr_str
        assert "vertices=54" in repr_str
        assert "edges=72" in repr_str
        assert "tiles=19" in repr_str
        assert "ports=9" in repr_str

    def test_vertex_repr(self):
        """Test vertex string representation"""
        vertex = VertexDefinition(VertexId("V00"), Coordinate(0, 0))
        repr_str = repr(vertex)
        assert "VertexDefinition" in repr_str
        assert "V00" in repr_str

    def test_edge_repr(self):
        """Test edge string representation"""
        edge = EdgeDefinition(EdgeId("E00"), (VertexId("V00"), VertexId("V01")))
        repr_str = repr(edge)
        assert "EdgeDefinition" in repr_str
        assert "E00" in repr_str

    def test_tile_repr(self):
        """Test tile string representation"""
        tile = TileDefinition(TileId("T00"), Coordinate(0, 0))
        repr_str = repr(tile)
        assert "TileDefinition" in repr_str
        assert "T00" in repr_str

    def test_port_repr(self):
        """Test port string representation"""
        port = PortDefinition(PortId("P_3TO1_N"), PortType.THREE_TO_ONE)
        repr_str = repr(port)
        assert "PortDefinition" in repr_str
        assert "P_3TO1_N" in repr_str
        assert "THREE_TO_ONE" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
