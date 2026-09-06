# Quick Reference Card

## Board Constants
```
Tiles: 19 (1 center + 6 ring1 + 12 ring2)
Vertices: 54 (settlement/city locations)
Edges: 72 (road locations)
Ports: 9 (6 × 3:1, 3 × 2:1)
```

## Resources
```python
ResourceType.WOOD, BRICK, SHEEP, WHEAT, ORE
Port.THREE_TO_ONE           # 3 of any → 1 of any
Port.TWO_TO_ONE_WOOD        # 2 wood → 1 of any
```

## Players
```python
PlayerId.P1, P2, P3, P4     # Exactly 4
Player order: P1 → P2 → P3 → P4 → P1 ...
```

## Development Cards
```
KNIGHT: 14              Used for Largest Army (3+ knights needed)
ROAD_BUILDING: 2        Place 2 free roads
YEAR_OF_PLENTY: 2       Take 2 resources from bank
MONOPOLY: 2             Call resource, all others give theirs
VICTORY_POINT: 5        Direct victory point
```

## Game Phases
```python
SETUP_FIRST     # First settlement placement
SETUP_SECOND    # Second placement (reverse order)
NORMAL_PLAY     # Standard turns with dice
GAME_OVER       # Winner determined
```

## Victory Conditions
```
SETTLEMENTS: 1 point each
CITIES: 2 points each
DEV CARDS: 1 point each (VP cards)
LARGEST ARMY: 2 points (3+ knights)
LONGEST ROAD: 2 points (5+ segments)
WIN: First to 10 points
```

## Resource Availability
```python
Bank (19 of each):     19 WOOD, 19 BRICK, 19 SHEEP, 19 WHEAT, 19 ORE
Bank (dev cards):      14 KNIGHT, 2 ROAD_BUILDING, 2 YEAR_OF_PLENTY
                       2 MONOPOLY, 5 VICTORY_POINT
Player Starting Res:   0 (gain from setup placements)
```

## Building Limits Per Player
```
Roads: 15 maximum
Settlements: 5 maximum
Cities: 4 maximum (upgrades settlement)
Development Cards: 1 per turn (buy limit)
```

## Turn Order in Setup
```
SETUP_FIRST (normal order):
  P1 places settlement + road
  P2 places settlement + road
  P3 places settlement + road
  P4 places settlement + road

SETUP_SECOND (reverse order):
  P4 places settlement + road (gets starting resources)
  P3 places settlement + road (gets starting resources)
  P2 places settlement + road (gets starting resources)
  P1 places settlement + road (gets starting resources)

Then normal play begins with P1
```

## Turn Phases (Normal Play)
```
1. PRE_ROLL    — Check playable dev cards, pass priority
2. ROLL        — Roll 2 dice
3. ROLLED      — Distribute resources, robber handling (on 7)
4. PLAYING     — Take actions (build, trade, play dev cards)
5. END_TURN    — End turn, next player's PRE_ROLL
```

## Adjacency Rules
- Settlements must be 2+ edges apart
- A settlement cannot have adjacent settlements
- Roads must connect to own settlements/cities/roads
- No crossing opponent roads

## Port Rules
```
Coastal Settlement: Access port's ratio
Port Location: On edge connecting 2 vertices
Port Types:
  • 3:1 ports (generic) - 6 on board
  • 2:1 resource ports - 3 on board (one per resource type)
Note: Board in spec has 3 × 2:1, 6 × 3:1 (total 9)
```

## Import Examples
```python
# Game creation
from src.simulation import Simulator
sim = Simulator(seed=42)

# Accessing board
from src.board import BoardGeometry
board = sim.board_geometry
vertex = board.get_vertex(VertexId("V00"))

# Player state
from src.core import PlayerState
player = PlayerState(PlayerId.P1)
player.victory_points = player.get_calculated_victory_points()

# Game state queries
game.is_setup_phase()
game.is_normal_play_phase()
game.is_game_over()
```

## File Locations
```
Source:       src/
Tests:        tests/
Docs:         docs/
Spec:         catan-simulator-agent-spec/
Board Geom:   src/board/board_geometry.py
Game State:   src/core/game_state.py
Player State: src/core/player_state.py
Types/Enums:  src/simulator/types/
```

## Test Commands
```bash
# All tests
pytest tests/ -v

# Domain types only
pytest tests/test_domain_types.py -v

# Board geometry only
pytest tests/test_board_geometry.py -v

# Specific test
pytest tests/test_board_geometry.py::TestBoardGeometry::test_board_creation -v
```

## Key Invariants
✅ Exactly 4 players (P1, P2, P3, P4)
✅ Exactly 19 tiles, 54 vertices, 72 edges
✅ Exactly 9 ports (distribution: 6 × 3:1, 3 × 2:1)
✅ Board topology immutable after creation
✅ All IDs unique within their type
✅ No dangling references between objects
✅ State calculated on-demand (victory points, etc.)

## Common Patterns

### Check if player can build
```python
player = game.get_player(PlayerId.P1)
if player.settlements_remaining > 0:
    # Can build settlement
```

### Get player's total resources
```python
total = player.get_total_resources()
has_wood = player.resources[ResourceType.WOOD] > 0
```

### Victory point calculation
```python
vp = player.get_calculated_victory_points()
if vp >= 10:
    game.winner = player.player_id
```

### Check game status
```python
if game.is_game_over():
    print(f"Winner: {game.winner.value}")
```

---

**For complete documentation, see `docs/` folder**
