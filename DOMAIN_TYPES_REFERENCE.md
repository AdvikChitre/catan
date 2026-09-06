# Domain Types Reference

Quick reference for all domain types implemented in Step 2.

## Imports Cheat Sheet

```python
# Enums
from src.simulator.types.resource import (
    ResourceType,           # WOOD, BRICK, SHEEP, WHEAT, ORE
    DevelopmentCardType,    # KNIGHT, ROAD_BUILDING, YEAR_OF_PLENTY, MONOPOLY, VICTORY_POINT
    PortType                # THREE_TO_ONE, TWO_TO_ONE_*
)

# Identifiers
from src.simulator.types.identifiers import (
    PlayerId,               # P1, P2, P3, P4
    BuildingType,           # SETTLEMENT, CITY
    Coordinate,             # 2D coordinates
    TileId, VertexId, EdgeId, PortId  # Type aliases
)

# Building types
from src.core.building import (
    Building,               # Settlement/City/Empty
    Road,                   # Road/Empty
    VertexState,            # Vertex with building
    EdgeState,              # Edge with road
    TileState               # Tile with resource and number
)

# State classes
from src.core import (
    GameState,
    GamePhase,
    GameStatus,
    BoardState,
    PlayerState,
    BankState,
    TurnState
)
```

## Common Patterns

### Creating a Player
```python
from src.core import PlayerState
from src.simulator.types.identifiers import PlayerId

player = PlayerState(PlayerId.P1)
player.resources[ResourceType.WOOD] = 5
player.settlements.add("vertex_1")
vp = player.get_calculated_victory_points()
```

### Creating Buildings
```python
from src.core.building import Building

settlement = Building.settlement(PlayerId.P1)  # 1 VP
city = Building.city(PlayerId.P1)              # 2 VP
empty = Building.empty()                       # 0 VP
```

### Checking Game Phase
```python
game = GameState()
if game.is_setup_phase():
    # Setup phase
elif game.is_normal_play_phase():
    # Normal play
elif game.is_game_over():
    # Game over
```

### Bank Operations
```python
from src.core import BankState
from src.simulator.types.resource import ResourceType

bank = BankState()
if bank.has_resource(ResourceType.WOOD, 1):
    # Can trade for wood
```

### Victory Point Calculation
```python
# Automatic calculation from state
vp = player.get_calculated_victory_points()

# Components:
# - 1 point per settlement
# - 2 points per city
# - 1 point per victory point dev card
# - 2 points if has largest army
# - 2 points if has longest road
```

## Constants

### Resource Counts
- Bank starts with: 19 of each resource (95 total)
- Development card deck: 25 cards total
  - Knight: 14
  - Road Building: 2
  - Year of Plenty: 2
  - Monopoly: 2
  - Victory Point: 5

### Player Limits
- Roads: 15 total
- Settlements: 5 total
- Cities: 4 total
- Victory to win: 10 points (can vary by house rules)

### Board Geometry
- Vertices: 54
- Edges: 72
- Tiles: 19
- Ports: 9

## Testing

Run all domain type tests:
```bash
python -m pytest tests/test_domain_types.py -v
```

Run specific test class:
```bash
python -m pytest tests/test_domain_types.py::TestPlayerState -v
```

Run specific test:
```bash
python -m pytest tests/test_domain_types.py::TestPlayerState::test_calculated_victory_points -v
```
