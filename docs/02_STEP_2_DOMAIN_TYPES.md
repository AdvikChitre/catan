# Step 2: Domain Types - Complete ✅

## Overview
Implemented all core domain types, enums, and state classes with comprehensive unit tests (36 tests, all passing).

## Implemented Components

### 1. Enums (src/simulator/types/resource.py)

#### ResourceType
- `WOOD`, `BRICK`, `SHEEP`, `WHEAT`, `ORE`
- Helper method: `tradeable_resources()` returns all 5 resources

#### DevelopmentCardType
- `KNIGHT` (14 in deck)
- `ROAD_BUILDING` (2 in deck)
- `YEAR_OF_PLENTY` (2 in deck)
- `MONOPOLY` (2 in deck)
- `VICTORY_POINT` (5 in deck)

#### PortType
- `THREE_TO_ONE` - Exchange 3 of any resource
- `TWO_TO_ONE_*` - Resource-specific 2:1 ports (WOOD, BRICK, SHEEP, WHEAT, ORE)
- Methods: `is_two_to_one()`, `get_resource_type()`

### 2. Identifiers (src/simulator/types/identifiers.py)

#### PlayerId Enum
- `P1`, `P2`, `P3`, `P4` (exactly 4 players)
- Helper: `all_players()` returns ordered list

#### BuildingType Enum
- `SETTLEMENT` (1 victory point)
- `CITY` (2 victory points)

#### Type Aliases
- `TileId` - Unique tile identifier
- `VertexId` - Unique vertex (settlement/city location) identifier
- `EdgeId` - Unique edge (road location) identifier
- `PortId` - Unique port identifier

#### Coordinate Class
- 2D coordinates for Catan board vertices
- Hashable and sortable
- String representation: `Coordinate(x, y)`

### 3. Building State (src/core/building.py)

#### Building Class
```python
Building
├── .type: BuildingType | None
├── .owner: PlayerId | None
├── is_empty() → bool
├── get_victory_points() → int (0, 1, or 2)
├── static empty() → Building
├── static settlement(owner) → Building
└── static city(owner) → Building
```

#### Road Class
```python
Road
├── .owner: PlayerId | None
├── is_empty() → bool
└── static empty() → Road
```

#### VertexState Class
```python
VertexState
├── .vertex_id: str
└── .building: Building
```

#### EdgeState Class
```python
EdgeState
├── .edge_id: str
└── .road: Road
```

#### TileState Class
```python
TileState
├── .tile_id: str
├── .resource_type: ResourceType
├── .number_token: int | None (None for desert)
└── .has_robber: bool
```

### 4. Board State (src/core/board_state.py)

```python
BoardState
├── .tiles: Dict[TileId, TileState]
├── .vertices: Dict[VertexId, VertexState]
├── .edges: Dict[EdgeId, EdgeState]
├── .robber_tile_id: TileId | None
├── get_tile(tile_id) → TileState | None
├── get_vertex(vertex_id) → VertexState | None
└── get_edge(edge_id) → EdgeState | None
```

### 5. Player State (src/core/player_state.py)

```python
PlayerState
├── .player_id: PlayerId
├── .resources: Dict[ResourceType, int]
├── .development_cards: Dict[DevelopmentCardType, int]
├── .played_development_cards: Set[DevelopmentCardType]
├── .roads: Set[EdgeId]
├── .settlements: Set[VertexId]
├── .cities: Set[VertexId]
├── .victory_points: int
├── .largest_army_count: int
├── .has_largest_army: bool
├── .has_longest_road: bool
├── .roads_remaining: int (up to 15)
├── .settlements_remaining: int (up to 5)
├── .cities_remaining: int (up to 4)
├── get_total_resources() → int
├── get_total_development_cards() → int
├── get_settlement_count() → int
├── get_city_count() → int
├── get_road_count() → int
└── get_calculated_victory_points() → int
    (settlements + cities + dev cards + achievements)
```

### 6. Bank State (src/core/bank_state.py)

```python
BankState
├── .resources: Dict[ResourceType, int]
│   └── Initially: 19 of each resource
├── .development_cards: Dict[DevelopmentCardType, int]
│   ├── KNIGHT: 14
│   ├── ROAD_BUILDING: 2
│   ├── YEAR_OF_PLENTY: 2
│   ├── MONOPOLY: 2
│   └── VICTORY_POINT: 5
├── get_total_resources() → int (95 initially)
├── get_total_development_cards() → int (25 initially)
├── has_resource(type, amount) → bool
└── has_development_card(type) → bool
```

### 7. Turn State (src/core/turn_state.py)

```python
TurnState
├── .current_player: PlayerId | None
├── .turn_number: int
├── .dice_roll: int | None
├── .phase: str (PRE_ROLL, ROLLED, PLAYING, END_TURN)
├── is_pre_roll() → bool
├── is_rolled() → bool
└── is_playing() → bool
```

### 8. Game State (src/core/game_state.py)

```python
GamePhase (Enum)
├── SETUP_FIRST
├── SETUP_SECOND
├── NORMAL_PLAY
└── GAME_OVER

GameStatus (Enum)
├── ACTIVE
├── COMPLETED
└── ERROR

GameState
├── .game_id: str
├── .seed: int
├── .phase: GamePhase
├── .status: GameStatus
├── .board_state: BoardState | None
├── .bank_state: BankState | None
├── .players: List[PlayerState]
├── .turn_state: TurnState | None
├── .creation_timestamp: float
├── .winner: PlayerId | None
├── get_player(player_id) → PlayerState | None
├── get_player_order() → List[PlayerId]
├── is_setup_phase() → bool
├── is_normal_play_phase() → bool
└── is_game_over() → bool
```

### 9. Type Aliases

```python
ResourceCount = Dict[ResourceType, int]
DevelopmentCardCount = Dict[DevelopmentCardType, int]
```

## Test Coverage

Created comprehensive test suite in `tests/test_domain_types.py`:

### Test Classes (36 tests total)
1. **TestResourceTypes** (2 tests)
   - All resources defined
   - Tradeable resources list

2. **TestDevelopmentCardTypes** (2 tests)
   - All card types defined
   - Correct count (5 types)

3. **TestPortTypes** (2 tests)
   - 3:1 port behavior
   - 2:1 ports with resource mapping

4. **TestPlayerId** (2 tests)
   - Exactly 4 players
   - Player values

5. **TestCoordinate** (4 tests)
   - Creation and equality
   - Hashing
   - Sorting

6. **TestBuilding** (4 tests)
   - Empty, settlement, city creation
   - Victory point calculation
   - Upgrade paths

7. **TestRoad** (2 tests)
   - Empty and owned roads

8. **TestPlayerState** (8 tests)
   - Creation and initial state
   - Resource tracking
   - Building counts
   - Victory point calculation
   - Largest army and longest road bonuses

9. **TestBankState** (4 tests)
   - Initial resource counts
   - Initial development cards
   - Resource and card availability checks

10. **TestBoardState** (1 test)
    - Creation

11. **TestTurnState** (2 tests)
    - Creation and phase checks

12. **TestGameState** (3 tests)
    - Creation
    - Phase and status checks

### Test Results
```
============================= 36 passed in 0.32s =============================
```

All tests passing ✅

## Key Design Decisions

1. **Enums over Strings**: Used Python Enums for all domain constants for type safety
2. **Type Aliases**: Used `NewType` for IDs to prevent mixing different ID types
3. **Builder Pattern**: Used static methods for Building/Road creation
4. **Calculation Methods**: Victory points calculated on-the-fly from state
5. **Immutable Collections**: Used Set for collections that don't need ordering
6. **Type Hints**: Full type hints on all methods for IDE support
7. **String Representations**: All classes have `__repr__` for debugging

## Next Steps: Step 3 - Board Geometry

Step 3 will implement:
- 54 canonical vertices with coordinates
- 72 canonical edges
- 19 canonical tiles
- Port definitions
- Adjacency relationships
- Comprehensive topology tests
