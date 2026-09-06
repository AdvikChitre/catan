# 3. Board Geometry and Setup

## 3.1 Canonical coordinate system

Keep the provided vertex coordinates:

```text
             (05)(15)(25)(35)(45)(55)(65)
       (04)(14)(24)(34)(44)(54)(64)(74)(84)
(03)(13)(23)(33)(43)(53)(63)(73)(83)(93)(103)
(02)(12)(22)(32)(42)(52)(62)(72)(82)(92)(102)
       (01)(11)(21)(31)(41)(51)(61)(71)(81)
             (00)(10)(20)(30)(40)(50)(60)
```

The implementation should create exactly the standard Catan topology:

- 54 vertices.
- 72 edges.
- 19 tiles.
- Standard port locations.

Validate these counts in tests.

## 3.2 Public coordinates

Bots use vertex coordinates when the public API exposes a location.

Example:

```ts
type VertexRef = {
  coordinate: Coordinate;
}
```

Internally the simulator may use numeric VertexIds for efficiency.

## 3.3 Canonical edges

Every edge connects two adjacent vertices.

Canonical equality:

```text edge(A, B) == edge(B, A)
```

The implementation must normalize endpoint ordering or otherwise guarantee uniqueness.

## 3.4 Tile adjacency

Each tile has exactly six vertices.

Each non-coastal vertex has the expected surrounding tile count from the topology.

The geometry builder must reject duplicate or invalid references.

## 3.5 Port representation

A Port consists of:

- PortId
- PortType
- two coastal vertices

A vertex may expose `portId` for convenience.

Port access is calculated from a player's building on either endpoint.

## 3.6 Board randomization

Setup must randomize tile contents using the simulator RNG.

Resources must be assigned as the standard tile distribution:

- 4 Wood
- 3 Brick
- 4 Sheep
- 4 Wheat
- 3 Ore
- 1 Desert

Number tokens must use the standard 18-token set:

2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12

The desert receives no number token.

The user's chosen policy is:

- randomize tile placement;
- assign probability tokens sequentially according to the canonical Catan token order.

Therefore the implementation must separate:

1. random tile/resource placement;
2. deterministic token sequence assignment.

The exact standard token ordering must be encoded once in a constant and tested.

The desert has no number token and starts with the robber.

If the selected setup algorithm skips the desert when placing tokens, do so deterministically.

## 3.7 Development-card deck

Create the standard 25-card development-card multiset:

- 14 Knight
- 5 Victory Point
- 2 Road Building
- 2 Year of Plenty
- 2 Monopoly

Shuffle it with the seeded RNG.

The top card is the next card drawn.

Never use framework-global shuffle functions that use uncontrolled randomness.

## 3.8 Initial player order

There are exactly four players.

The simulator receives/creates player order as:

```text
P1, P2, P3, P4
```

Initial settlement/road placement is snake order:

```text
P1
P2
P3
P4
P4
P3
P2
P1
```

## 3.9 Initial placement decision

For each placement, the simulator calculates legal settlement vertices and legal roads from that settlement.

The bot is asked to provide:

```ts
InitialPlacementAction {
  settlementVertex: VertexRef;
  roadEdge: EdgeRef;
}
```

The settlement and road are executed as one setup decision.

The road must legally connect to the newly placed settlement.

## 3.10 Second-settlement resources

After the second settlement for each player is placed, the simulator determines starting resources from the tiles adjacent to that settlement.

A settlement produces one card per adjacent producing tile.

The player receives those resources immediately.

Publish appropriate public resource-receipt events.

## 3.11 Setup restrictions

No development cards, normal trading, or normal turn actions occur during initial placement.

Use setup-specific action generation and validation.

## 3.12 Board state after setup

After setup:

- all eight initial settlement/road placements are recorded;
- each player has correct remaining pieces;
- robber remains on desert unless rules/setup dictate otherwise;
- initial resources have been awarded;
- current player is P1 for the first normal turn unless the chosen canonical start rule specifies another deterministic start. Use P1 for version 1.
