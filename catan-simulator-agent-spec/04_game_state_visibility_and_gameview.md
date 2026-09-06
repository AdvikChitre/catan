# 4. Game State Visibility and GameView

## 4.1 Core rule

Bots receive a fresh `GameView` for themselves at each decision request.

The GameView is:

- read-only;
- player-specific;
- a snapshot;
- generated from authoritative GameState.

## 4.2 No event history

GameView MUST NOT contain:

- complete event log;
- previous trade history;
- previous dice history unless it is an independently public current-state field;
- a replay transcript.

Bots learn about events through `OnEvent` and may choose what to remember.

## 4.3 GameView shape

Recommended:

```ts
interface GameView {
  gameId: string;
  self: SelfView;
  board: BoardView;
  opponents: OpponentView[];
  turn: TurnView;
}
```

## 4.4 SelfView

```ts
interface SelfView {
  playerId: PlayerId;
  resources: Readonly<ResourceCounts>;
  developmentCards: Readonly<DevelopmentCardCounts>;

  roadsRemaining: number;
  settlementsRemaining: number;
  citiesRemaining: number;

  knightsPlayed: number;
  victoryPoints: number;
  hasLongestRoad: boolean;
  hasLargestArmy: boolean;
}
```

## 4.5 OpponentView

```ts
interface OpponentView {
  playerId: PlayerId;

  roads: Readonly<EdgeView[]>;
  buildings: Readonly<VertexBuildingView[]>;

  knightsPlayed: number;

  victoryPoints: number;
  hasLongestRoad: boolean;
  hasLargestArmy: boolean;
}
```

Do NOT include opponent:

- resources;
- development-card identities;
- development-card counts;
- hidden Victory Point cards.

Opponent piece counts may be derived from visible pieces and need not be separately exposed.

## 4.6 BoardView

```ts
interface BoardView {
  tiles: readonly TileView[];
  vertices: readonly VertexView[];
  edges: readonly EdgeView[];
  ports: readonly PortView[];
  robberTileId: TileId;
}
```

## 4.7 TileView

```ts
interface TileView {
  tileId: TileId;
  resourceType: TileResourceType;
  numberToken: number | null;
  hasRobber: boolean;
}
```

All players can see the public tile configuration.

## 4.8 VertexView

```ts
interface VertexView {
  vertexId: VertexId;
  coordinate: Coordinate;
  building:
    | null
    | { type: "SETTLEMENT"; owner: PlayerId }
    | { type: "CITY"; owner: PlayerId };
  portId: PortId | null;
}
```

## 4.9 EdgeView

```ts
interface EdgeView {
  edgeId: EdgeId;
  vertexA: Coordinate;
  vertexB: Coordinate;
  roadOwner: PlayerId | null;
}
```

## 4.10 TurnView

```ts
interface TurnView {
  turnNumber: number;
  currentPlayer: PlayerId;
  phase: GamePhase;
}
```

## 4.11 Immutability

Do not expose references to mutable simulator internals.

Use:

- immutable records;
- deep copies;
- frozen objects;
- DTO serialization;

or an equivalent safe mechanism.

The important behavioural requirement is that bot code cannot mutate simulator state through GameView.

## 4.12 View creation

For every bot decision:

```text
authoritative GameState
      ↓
GameViewBuilder(playerId)
      ↓
player-specific GameView
```

Do not cache a previous GameView through multiple state mutations.

Create a new view after each completed action when the next bot decision is requested.

## 4.13 Private data boundary

The implementation should include tests that intentionally attempt to inspect available bot arguments and confirm that opponent private information is absent.
