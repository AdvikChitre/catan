# 3. Domain and Board

## Core types
Coordinate, PlayerId, TileId, VertexId, EdgeId, PortId,
ResourceType, DevelopmentCardType, Building,
BoardGeometry, BoardState, PlayerState, BankState, TurnState, GameState.

## Canonical board
- 19 tiles
- 54 vertices
- 72 edges

Vertex coordinate layout:
```text
             (05)(15)(25)(35)(45)(55)(65)
       (04)(14)(24)(34)(44)(54)(64)(74)(84)
(03)(13)(23)(33)(43)(53)(63)(73)(83)(93)(103)
(02)(12)(22)(32)(42)(52)(62)(72)(82)(92)(102)
       (01)(11)(21)(31)(41)(51)(61)(71)(81)
             (00)(10)(20)(30)(40)(50)(60)
```

## Geometry/state split

### BoardGeometry: immutable
Contains:
- vertex definitions
- edge definitions
- tile definitions
- port definitions
- adjacency

### BoardState: mutable
Contains:
- tile resource/number assignment
- building occupancy
- road ownership
- robber location

## Structures

```ts
interface VertexDefinition {
  id: VertexId;
  coordinate: Coordinate;
  adjacentVertexIds: VertexId[];
  adjacentEdgeIds: EdgeId[];
  adjacentTileIds: TileId[];
  portId: PortId | null;
}

interface EdgeDefinition {
  id: EdgeId;
  vertexA: VertexId;
  vertexB: VertexId;
}

interface TileDefinition {
  id: TileId;
  vertexIds: [VertexId, VertexId, VertexId, VertexId, VertexId, VertexId];
}

interface PortDefinition {
  id: PortId;
  type: PortType;
  vertexA: VertexId;
  vertexB: VertexId;
}
```

An edge is uniquely identified by its endpoint pair; reverse endpoint order is the same edge.

## Resources
4 Wood, 3 Brick, 4 Sheep, 4 Wheat, 3 Ore, 1 Desert.

## Number tokens
2,3,3,4,4,5,5,6,6,8,8,9,9,10,10,11,11,12.
Desert has no token.

## Development deck
14 Knight
5 Victory Point
2 Road Building
2 Year of Plenty
2 Monopoly

## Ports
3:1 plus five 2:1 specific-resource ports.
A building on either endpoint gives access.

## Player pieces
15 roads, 5 settlements, 4 cities.

## Setup
Snake order:
P1 P2 P3 P4 P4 P3 P2 P1.
Each placement = settlement + connected road.
Second settlement grants starting resources from adjacent producing tiles.
