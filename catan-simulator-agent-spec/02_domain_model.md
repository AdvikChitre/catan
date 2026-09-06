# 2. Domain Model

The implementation must use stable identifiers and typed values.

## 2.1 PlayerId

Use an integer or string identifier with exactly four valid players.

For deterministic ordering use:

```text
P1
P2
P3
P4
```

The exact in-memory type may be an enum.

## 2.2 Coordinate

```ts
interface Coordinate {
  x: number;
  y: number;
}
```

Two coordinates are equal when both x and y are equal.

Use the supplied Catan vertex coordinate system. Do not introduce a different public coordinate scheme.

## 2.3 ResourceType

```ts
enum ResourceType {
  WOOD,
  BRICK,
  SHEEP,
  WHEAT,
  ORE
}
```

Desert is a tile type, not a player resource.

## 2.4 DevelopmentCardType

```ts
enum DevelopmentCardType {
  KNIGHT,
  ROAD_BUILDING,
  YEAR_OF_PLENTY,
  MONOPOLY,
  VICTORY_POINT
}
```

## 2.5 Building

```ts
type Building =
  | { type: "NONE" }
  | { type: "SETTLEMENT"; owner: PlayerId }
  | { type: "CITY"; owner: PlayerId };
```

## 2.6 Road

```ts
interface EdgeState {
  owner: PlayerId | null;
}
```

## 2.7 PortType

```ts
enum PortType {
  THREE_TO_ONE,
  TWO_TO_ONE_WOOD,
  TWO_TO_ONE_BRICK,
  TWO_TO_ONE_SHEEP,
  TWO_TO_ONE_WHEAT,
  TWO_TO_ONE_ORE
}
```

## 2.8 TileState

```ts
interface TileState {
  tileId: TileId;
  resourceType: TileResourceType;
  numberToken: number | null;
}
```

`numberToken` is null for the desert.

The robber position is stored separately in BoardState; optionally a derived view may include `hasRobber`.

## 2.9 BoardState

```ts
interface BoardState {
  tiles: Map<TileId, TileState>;
  vertices: Map<VertexId, VertexState>;
  edges: Map<EdgeId, EdgeState>;
  robberTileId: TileId;
}
```

## 2.10 VertexState

```ts
interface VertexState {
  building:
    | { type: "NONE" }
    | { type: "SETTLEMENT"; owner: PlayerId }
    | { type: "CITY"; owner: PlayerId };
}
```

Geometry data for that vertex is kept in BoardGeometry, not duplicated in this state object.

## 2.11 BoardGeometry

Recommended conceptual structure:

```ts
interface BoardGeometry {
  vertices: Map<VertexId, VertexDefinition>;
  edges: Map<EdgeId, EdgeDefinition>;
  tiles: Map<TileId, TileDefinition>;
  ports: Map<PortId, PortDefinition>;
}
```

### VertexDefinition

```ts
interface VertexDefinition {
  id: VertexId;
  coordinate: Coordinate;
  adjacentVertexIds: VertexId[];
  adjacentEdgeIds: EdgeId[];
  adjacentTileIds: TileId[];
  portId: PortId | null;
}
```

### EdgeDefinition

```ts
interface EdgeDefinition {
  id: EdgeId;
  vertexA: VertexId;
  vertexB: VertexId;
}
```

### TileDefinition

```ts
interface TileDefinition {
  id: TileId;
  vertexIds: [VertexId, VertexId, VertexId, VertexId, VertexId, VertexId];
}
```

### PortDefinition

```ts
interface PortDefinition {
  id: PortId;
  type: PortType;
  vertexA: VertexId;
  vertexB: VertexId;
}
```

The exact canonical IDs are implementation data. Generate/validate the complete graph once and test it against expected counts and adjacency.

## 2.12 PlayerState

```ts
interface PlayerState {
  id: PlayerId;

  resources: ResourceCounts;
  developmentCards: DevelopmentCardCounts;

  roadsRemaining: number;
  settlementsRemaining: number;
  citiesRemaining: number;

  knightsPlayed: number;

  longestRoadLength: number;    // derived/cache only
  hasLongestRoad: boolean;      // derived/cache only
  hasLargestArmy: boolean;      // derived/cache only
  victoryPoints: number;        // derived/cache only
}
```

Do not treat derived/cache values as independent truth. Recalculate them after relevant state changes or use methods that derive them from authoritative state.

## 2.13 TurnState

```ts
interface TurnState {
  turnNumber: number;
  currentPlayer: PlayerId;

  phase:
    | "SETUP_FORWARD"
    | "SETUP_REVERSE"
    | "PRE_ROLL"
    | "ROLL_REQUIRED"
    | "POST_ROLL"
    | "ROBBER_DISCARD"
    | "ROBBER_MOVE"
    | "ROBBER_STEAL"
    | "TRADE_NEGOTIATION"
    | "SPECIAL_ACTION"
    | "GAME_OVER";
}
```

Implementation may use a richer internal state machine as long as externally visible behaviour matches this specification.

## 2.14 BankState

```ts
interface BankState {
  resources: ResourceCounts;
  developmentDeck: DevelopmentCardType[];
}
```

## 2.15 Count maps

```ts
type ResourceCounts = Record<ResourceType, number>;
type DevelopmentCardCounts =
  Record<DevelopmentCardType, number>;
```

Use zero entries instead of missing keys.

## 2.16 Piece supply

Standard player piece counts:

```text
roads: 15
settlements: 5
cities: 4
```

Track remaining pieces explicitly.
