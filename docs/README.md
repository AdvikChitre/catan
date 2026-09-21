# Catan Simulator Implementation Guide

This is the master documentation index for the Catan simulator project. All specification and implementation documentation is in the `docs/` folder.

## Quick Start

### View Progress
See [docs/00_PROGRESS.md](docs/00_PROGRESS.md) for implementation status across all 19 steps.

### Understand Project Structure
See [docs/01_PROJECT_STRUCTURE.md](docs/01_PROJECT_STRUCTURE.md) for module organization and architecture.

### Learn Domain Types
See [docs/02_STEP_2_DOMAIN_TYPES.md](docs/02_STEP_2_DOMAIN_TYPES.md) for complete enum and state class documentation.
See [docs/02_DOMAIN_TYPES_REFERENCE.md](docs/02_DOMAIN_TYPES_REFERENCE.md) for quick imports and patterns.

### Learn Board Geometry
See [docs/03_STEP_3_BOARD_GEOMETRY.md](docs/03_STEP_3_BOARD_GEOMETRY.md) for board topology and adjacency.

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run domain type tests (36 tests)
python -m pytest tests/test_domain_types.py -v

# Run board geometry tests (38 tests)
python -m pytest tests/test_board_geometry.py -v

# Run a specific test
python -m pytest tests/test_board_geometry.py::TestBoardGeometry::test_board_creation -v
```

## Implementation Order (from spec/)

The specification folder `catan-simulator-agent-spec/` contains 14 detailed requirements documents:

1. ✅ **00_README.md** — Project overview and fundamental invariants
2. ✅ **01_scope_and_architecture.md** — Component responsibilities
3. ✅ **02_domain_model.md** — Type and enum definitions
4. ✅ **03_board_geometry_and_setup.md** — Board topology (54 vertices, 72 edges, 19 tiles)
5. **04_game_state_visibility_and_gameview.md** — Hidden information filtering
6. **05_bot_api_and_actions.md** — Bot interface contract
7. **06_events.md** — Event publishing system
8. **07_turn_state_machine.md** — Turn phases and transitions
9. **08_rules_and_transactions.md** — Rule enforcement
10. **09_determinism_timeouts_errors_replay.md** — Error handling and replay
11. **10_web_contract.md** — Web API design
12. **11_testing_and_acceptance.md** — Test strategy
13. **12_implementation_order.md** — Step-by-step build order
14. **13_decision_log.md** — Design decisions
15. **14_AGENT_EXECUTION_PROMPT.md** — Agent instructions

## Current Implementation Status

### Completed (3 of 19 Steps)

**Step 1: Project Skeleton** ✅
- Module structure: 10 packages
- Entry point: `src/simulator/run.py`
- Package files: 25+ __init__.py files

**Step 2: Domain Types** ✅
- Enums: ResourceType, DevelopmentCardType, PortType, PlayerId, BuildingType
- State classes: GameState, PlayerState, BankState, BoardState, TurnState
- Building classes: Building, Road, VertexState, EdgeState, TileState
- Tests: 36 unit tests, 100% passing

**Step 3: Board Geometry** ✅
- 19 tiles with axial coordinates
- 54 vertices with topology
- 72 edges connecting vertices
- 9 ports (6 × 3:1, 3 × 2:1)
- Tests: 38 unit tests, 100% passing

### Next Up (Steps 4-19)

**Step 4: Seeded RNG** ⏳
- Deterministic random number generator
- Seed reproducibility
- Foundation for board randomization

**Step 5: Board Setup** ⏳
- Tile resource randomization
- Number token distribution
- Development card shuffling

...and 12 more steps through complete game implementation and web integration.

## Key Architectural Decisions

### Immutable Geometry
The `BoardGeometry` class is immutable once constructed, ensuring topology never changes during gameplay. This prevents bugs and makes reasoning about the board simple.

### Type Safety
Uses Python's `NewType` and `Enum` for all identifiers and constants, preventing bugs like confusing vertex IDs with edge IDs.

### State Separation
- **Immutable**: BoardGeometry (topology)
- **Mutable**: GameState, PlayerState, BoardState (gameplay)

This prevents accidental mutations of the board layout while allowing dynamic game state.

### No Side Effects
All components are pure functions with clear inputs/outputs. The Simulator is the only orchestrator calling these functions.

### Strong Type Hints
Full type annotations throughout enable IDE support, type checking, and self-documenting code.

## Testing Strategy

### Unit Tests (74 total)
- Domain type invariants (36 tests)
- Board topology validation (38 tests)

### Integration Tests (coming)
- Setup phase workflows
- Turn state machine transitions
- Action generation and validation
- Event ordering and publishing
- Bot decision handling

### End-to-End Tests (coming)
- Complete game simulations with deterministic outcomes
- Replay validation
- Web contract compliance

## Important Concepts

### PlayerId
Exactly 4 players: P1, P2, P3, P4. Used throughout for player tracking and turn order.

### Coordinates
Axial coordinates (x, y) for board positions. Hashable and sortable for consistent ordering.

### Ports
Located at exactly 2 adjacent vertices (coastal positions). Enable advantageous resource trading.

### Victory Points
Automatically calculated from: settlements (1 each) + cities (2 each) + dev cards + achievements (largest army 2, longest road 2).

### Development Cards
Deck of 25: 14 knights, 2 road buildings, 2 year of plenty, 2 monopoly, 5 victory points.

## Dependencies

**Only standard library used:**
- `enum` — Enums
- `typing` — Type hints
- `random` — RNG (will be seeded)
- `pytest` — Testing (development only)

No external dependencies keeps the code simple and portable.

## Future Extensions

This foundation supports:
1. Different board layouts (Seafarers, expansions)
2. Variable player counts (with rule adjustments)
3. AI bots (implementing BotInterface)
4. Web UI (consuming replay data)
5. Network play (via web transport layer)

## Getting Help

1. **Architecture questions**: See `01_scope_and_architecture.md`
2. **Type questions**: See `02_DOMAIN_TYPES_REFERENCE.md`
3. **Board questions**: See `03_STEP_3_BOARD_GEOMETRY.md`
4. **Specification questions**: See `catan-simulator-agent-spec/`
5. **Code questions**: Check type hints and docstrings

## Contributing

When implementing new steps:
1. Read the corresponding spec document
2. Check the implementation order
3. Create comprehensive unit tests first (TDD)
4. Add documentation in `docs/` folder
5. Ensure all tests pass
6. Keep strong type hints
7. Maintain immutability where specified

---

**Last Updated**: Step 3 Complete
**Tests**: 74/74 passing ✅
**Next Step**: Step 4 - Seeded RNG
