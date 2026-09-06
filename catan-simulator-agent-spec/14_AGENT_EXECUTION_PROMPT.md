# Agent Execution Instructions

You are implementing the Catan Bot Simulator described by the specification files in this directory.

## Before coding

Read ALL specification files.

Do not start by writing the web UI.

First understand:

- authoritative state;
- immutable board geometry;
- GameView privacy boundary;
- bot callback direction;
- action generation;
- event delivery;
- turn state machine;
- deterministic RNG.

## Priority

Correctness and determinism are more important than cleverness or premature abstraction.

Do not invent game rules where the specification explicitly defines them.

Do not simplify away:

- hidden information;
- event delivery;
- trade counters;
- seeded randomness;
- action generation;
- graph-based road rules.

## Implementation strategy

Implement in the order in `12_implementation_order.md`.

At every stage:

1. create the smallest correct implementation;
2. add focused tests;
3. run the complete test suite;
4. preserve already-established public contracts.

## Do not expose hidden state

Never pass a raw simulator, raw GameState, BankState, mutable PlayerState, or another bot object to a bot.

All bot-facing state must pass through the defined GameView/request DTO boundary.

## Do not move strategy into the simulator

The simulator must not decide that a trade is strategically good, choose where a bot should build, or otherwise play for a bot.

It only supplies legal choices and executes the bot's chosen decisions.

## Determinism

No direct calls to uncontrolled random APIs.

All randomness must flow through the per-game seeded RNG.

No reliance on map/object iteration order where event ordering or game outcomes can be affected.

## When a specification detail is ambiguous

Prefer, in order:

1. an explicit locked decision in `13_decision_log.md`;
2. an exact interface/type definition;
3. the explicit rule text;
4. standard Catan rules for the scoped four-player game.

Do not introduce variants.

## Definition of done

Do not declare the implementation complete until the acceptance criteria in `11_testing_and_acceptance.md` pass, including:

- full games;
- privacy tests;
- trade transactions;
- all development cards;
- robber;
- Longest Road;
- Largest Army;
- timeout/error behaviour;
- deterministic replay.

## Output

At completion, provide:

- implementation summary;
- test summary;
- list of public bot API types;
- list of simulator entry points;
- web/replay integration points;
- any remaining explicitly documented limitations.

Do not hide known failures.
