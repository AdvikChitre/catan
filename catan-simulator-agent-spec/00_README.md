# Catan Bot Simulator — Agent Implementation Specification

## Purpose

This directory is the implementation contract for a simulator that runs four Catan bots against each other.

This specification is intentionally explicit. The implementation agent MUST follow the external behaviour and interfaces defined here rather than inventing alternative game semantics.

The simulator is the authority over all game state and rules. Bots are strategy implementations that are instantiated by the simulator, receive restricted read-only views, and return decisions.

## Scope

Implement standard four-player Catan only.

Include:

- 4 players exactly.
- Standard 19-hex Catan board.
- Standard resources.
- Standard number tokens.
- Desert and robber.
- Roads, settlements, cities.
- Ports.
- Resource production.
- Dice.
- Roll-7 discard rule.
- Robber movement and random stealing.
- Knight.
- Road Building.
- Year of Plenty.
- Monopoly.
- Victory Point cards.
- Longest Road.
- Largest Army.
- Standard initial placement.
- Player-to-player trading.
- Counter-offers.
- Bank trading.
- Event publication.
- Player-specific hidden-information views.
- Deterministic seeded randomness.
- Three-second bot decision limit.
- Replay/event output suitable for a separate web client.

## Explicit non-goals

Do NOT implement in version 1:

- Catan expansions.
- Seafarers.
- Cities & Knights.
- 5-6 player rules.
- Variants.
- AI strategy.
- A built-in bot implementation beyond simple test bots.
- A requirement that bots expose their internal memory.
- A server-side event-history API inside GameView.

## Source of truth

The following precedence applies if documents appear to conflict:

1. This README and explicit acceptance criteria.
2. Exact API/type definitions.
3. Explicit state-machine/rule requirements.
4. Explanatory text.

Where an implementation detail is not externally observable, the agent may choose a reasonable implementation.

## Reference technology

Use a strongly typed implementation. The examples in this specification use TypeScript-like syntax because the simulator is intended to have a web interface.

Recommended separation:

- simulator core: TypeScript library running server-side
- bot runner/sandbox: server-side process boundary
- web application: separate client consuming simulator/replay data

Do not make the core simulator depend on the web UI.

## Fundamental invariants

- Bots never receive the raw Simulator instance.
- Bots never receive raw mutable GameState.
- Bots never receive the Bank.
- Bots never receive opponent private resources or development-card hands.
- GameView contains current observable state, not event history.
- Events are delivered in real time through OnEvent.
- The simulator calls bots; bots do not call simulator methods.
- All state mutation happens inside the simulator.
- All random behaviour comes from the seeded simulator RNG.
- AvailableActions are generated from the current authoritative state.
- The simulator still validates bot responses defensively.
- Every successful state mutation can produce corresponding events.
- A single deterministic logical event order is maintained.

## Directory guide

- `01_scope_and_architecture.md` — component responsibilities and boundaries.
- `02_domain_model.md` — exact core data structures.
- `03_board_geometry_and_setup.md` — board topology, coordinates, setup.
- `04_game_state_visibility_and_gameview.md` — hidden/public state and views.
- `05_bot_api_and_actions.md` — bot methods and action types.
- `06_events.md` — event catalogue and visibility.
- `07_turn_state_machine.md` — exact game/turn control flow.
- `08_rules_and_transactions.md` — game rules and trade transactions.
- `09_determinism_timeouts_errors_replay.md` — RNG, timeouts, errors, replay.
- `10_web_contract.md` — interface between simulator and web UI.
- `11_testing_and_acceptance.md` — required tests and done criteria.
- `12_implementation_order.md` — exact implementation sequence.
