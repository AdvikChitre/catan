# Catan Simulator - Project Structure

## Directory Layout

```
src/
├── __init__.py                 # Package root
├── core/                       # Domain model and state
│   ├── __init__.py
│   ├── game_state.py          # Complete game state
│   ├── board_state.py         # Mutable board state
│   ├── player_state.py        # Player information
│   ├── bank_state.py          # Resource pool and dev cards
│   └── turn_state.py          # Current turn info
├── board/                      # Board geometry
│   ├── __init__.py
│   ├── board_geometry.py      # Immutable topology
│   ├── tile.py                # Tile definitions
│   └── port.py                # Port definitions
├── rules/                      # Game rules
│   ├── __init__.py
│   └── rules_engine.py        # Rules queries
├── actions/                    # Action system
│   ├── __init__.py
│   ├── action_types.py        # Action definitions
│   └── action_generator.py    # Legal action generation
├── views/                      # Player-specific views
│   ├── __init__.py
│   ├── game_view.py           # Player view
│   └── game_view_builder.py   # View construction
├── bots/                       # Bot system
│   ├── __init__.py
│   ├── bot_interface.py       # Bot interface contract
│   └── bot_manager.py         # Bot lifecycle
├── events/                     # Event system
│   ├── __init__.py
│   ├── game_event.py          # Event types
│   └── event_bus.py           # Event publishing
├── simulation/                 # Main simulator
│   ├── __init__.py
│   ├── simulator.py           # Orchestrator
│   └── seeded_rng.py          # Deterministic RNG
├── replay/                     # Replay recording
│   ├── __init__.py
│   └── replay_recorder.py     # Event recording
├── web_transport/              # Web API
│   ├── __init__.py
│   └── game_contract.py       # API contracts
└── simulator/
    ├── __init__.py
    ├── run.py                 # Entry point
    └── types/
        ├── __init__.py
        ├── resource.py        # ResourceType enum
        └── identifiers.py     # PlayerId, Coordinates, IDs
```

## Step 1: Project Skeleton - Complete

✅ Module structure established
✅ Package initialization files created
✅ Core domain types defined
✅ Placeholder implementations for all major components
✅ Entry point ready for Step 2

### Key Components Established:

1. **core/** - GameState, PlayerState, BoardState, BankState, TurnState
2. **board/** - BoardGeometry, Tile, Port
3. **rules/** - RulesEngine base
4. **actions/** - Action types and ActionGenerator
5. **views/** - GameView and GameViewBuilder
6. **bots/** - BotInterface and BotManager
7. **events/** - GameEvent and EventBus
8. **simulation/** - Simulator orchestrator and SeededRng
9. **replay/** - ReplayRecorder
10. **web_transport/** - GameContract
11. **simulator/types/** - ResourceType, PlayerId, Identifiers

### Ready for Next Step:

Step 2 will implement detailed domain types with unit tests for:
- Complete enums (ResourceType, DevelopmentCardType, PortType, etc.)
- Domain DTOs with proper validation
- Count maps for resources and development cards
