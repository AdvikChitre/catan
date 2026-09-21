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


class GeometryValue:
    def __setattr__(self, name, value):
        if getattr(self, '_sealed', False):
            raise TypeError('Board geometry is immutable')
        object.__setattr__(self, name, value)

    def seal(self):
        for key,value in vars(self).copy().items():
            if isinstance(value,set): object.__setattr__(self,key,frozenset(value))
        object.__setattr__(self,'_sealed',True)


class VertexDefinition(GeometryValue):
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


class EdgeDefinition(GeometryValue):
    """Immutable edge topology"""
    def __init__(self, edge_id: EdgeId, vertex_ids: Tuple[VertexId, VertexId]):
        self.id = edge_id
        self.vertex_ids: Set[VertexId] = set(vertex_ids)

    def __repr__(self):
        return f"EdgeDefinition({self.id})"


class TileDefinition(GeometryValue):
    """Immutable tile topology"""
    def __init__(self, tile_id: TileId, coordinate: Coordinate):
        self.id = tile_id
        self.coordinate = coordinate
        self.vertex_ids: Set[VertexId] = set()
        self.edge_ids: Set[EdgeId] = set()

    def __repr__(self):
        return f"TileDefinition({self.id}, {self.coordinate})"


class PortDefinition(GeometryValue):
    """Immutable port definition"""
    def __init__(self, port_id: PortId, port_type: PortType):
        self.id = port_id
        self.port_type = port_type
        self.vertex_ids: Set[VertexId] = set()  # Two vertices where port is located

    def __repr__(self):
        return f"PortDefinition({self.id}, {self.port_type.value})"


class BoardGeometry(GeometryValue):
    """Immutable topology of the canonical 19-tile Catan board"""
    
    def __init__(self):
        import math
        from collections import Counter
        self.tiles, self.vertices, self.edges, self.ports = {}, {}, {}, {}
        # Stable axial tile IDs retained for recordings. Pointy hex corners use
        # integer lattice coordinates; Cartesian conversion happens only once.
        coords = [(0,0),(1,0),(1,-1),(0,-1),(-1,0),(-1,1),(0,1),
                  (2,0),(2,-1),(2,-2),(1,-2),(0,-2),(-1,-1),(-2,0),
                  (-2,1),(-2,2),(-1,2),(0,2),(1,1)]
        names = ['T00']+[f'T1{i}' for i in range(6)]+[f'T{20+i}' for i in range(12)]
        corners = [(1,-1),(1,1),(0,2),(-1,1),(-1,-1),(0,-2)]
        tile_points = {name: [(2*q+r+dx,3*r+dy) for dx,dy in corners]
                       for name,(q,r) in zip(names,coords)}
        points = sorted({p for ps in tile_points.values() for p in ps}, key=lambda p:(p[1],p[0]))
        ids = {p: VertexId(f'V{i:02d}') for i,p in enumerate(points)}
        for (x,y),vid in ids.items():
            self.vertices[vid] = VertexDefinition(vid,Coordinate(x*math.sqrt(3)/2,y/2))
        pairs = sorted({tuple(sorted((ids[ps[i]],ids[ps[(i+1)%6]])))
                        for ps in tile_points.values() for i in range(6)})
        edge_ids = {pair: EdgeId(f'E{i:02d}') for i,pair in enumerate(pairs)}
        for pair,eid in edge_ids.items():
            self.edges[eid] = EdgeDefinition(eid,pair)
            a,b=pair
            self.vertices[a].adjacent_vertex_ids.add(b)
            self.vertices[b].adjacent_vertex_ids.add(a)
            for v in pair: self.vertices[v].adjacent_edge_ids.add(eid)
        uses=Counter()
        for name,coord in zip(names,coords):
            tile=TileDefinition(TileId(name),Coordinate(*coord))
            vs=[ids[p] for p in tile_points[name]]
            tile.vertex_ids.update(vs)
            for i,v in enumerate(vs):
                self.vertices[v].adjacent_tile_ids.add(tile.id)
                eid=edge_ids[tuple(sorted((v,vs[(i+1)%6])))]
                tile.edge_ids.add(eid)
                uses[eid]+=1
            self.tiles[tile.id]=tile
        # Walk the 30 coastal edges; space nine non-overlapping ports around it.
        coastal={e for e,n in uses.items() if n==1}
        start=min(v for e in coastal for v in self.edges[e].vertex_ids)
        current=start; previous=None; coast=[]
        while len(coast)<30:
            choices=sorted(e for e in self.vertices[current].adjacent_edge_ids
                           if e in coastal and e!=previous)
            eid=choices[0]; coast.append(eid)
            current=next(v for v in self.edges[eid].vertex_ids if v!=current)
            previous=eid
        types=[PortType.THREE_TO_ONE,PortType.TWO_TO_ONE_WOOD,
               PortType.THREE_TO_ONE,PortType.TWO_TO_ONE_BRICK,
               PortType.TWO_TO_ONE_SHEEP,PortType.THREE_TO_ONE,
               PortType.TWO_TO_ONE_WHEAT,PortType.THREE_TO_ONE,PortType.TWO_TO_ONE_ORE]
        for i,(offset,kind) in enumerate(zip([0,3,6,10,13,16,20,23,26],types)):
            pid=PortId('P_3TO1_N' if i==0 else f'PORT{i}')
            port=PortDefinition(pid,kind)
            port.vertex_ids.update(self.edges[coast[offset]].vertex_ids)
            self.ports[pid]=port
            for vid in port.vertex_ids: self.vertices[vid].port_id=pid
        from types import MappingProxyType
        for name in ('vertices','edges','tiles','ports'):
            objects=getattr(self,name)
            for item in objects.values(): item.seal()
            setattr(self,name,MappingProxyType(objects))
        self.seal()

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
