# 12. Implementation Order

Follow this order. Do not jump directly to the full game loop.

## Step 1 — Project skeleton

Create separate modules/packages for:

```text
core model
board
rules
actions
views
bots
events
simulation
replay
web transport
```

The simulator core must build and run without the web frontend.

## Step 2 — Domain types

Implement:

- identifiers;
- enums;
- count maps;
- domain DTOs;
- GameState;
- BoardState;
- PlayerState;
- BankState;
- TurnState.

Add unit tests.

## Step 3 — Board geometry

Implement canonical graph.

Build:

- 54 vertices;
- 72 edges;
- 19 tiles;
- ports.

Add adjacency tests.

Do not implement game play yet.

## Step 4 — Seeded RNG

Implement a deterministic RNG abstraction.

Write tests proving identical seeds produce identical integer sequences.

All later random logic must depend on this abstraction.

## Step 5 — Board setup

Implement:

- tile/resource randomization;
- sequential number tokens;
- desert;
- robber;
- development-card deck shuffle.

Add reproducibility tests.

## Step 6 — GameViewBuilder

Implement private/public visibility before implementing bots.

Construct player-specific views.

Write deliberate hidden-information tests.

## Step 7 — Event system

Implement:

- event DTOs;
- sequence counter;
- EventBus;
- visibility filters;
- ReplayRecorder.

Write event-order tests.

## Step 8 — Basic bot interface

Implement a dummy test bot.

Simulator instantiates exactly four bots and calls them through the defined interface.

Verify no raw GameState is exposed.

## Step 9 — Setup state machine

Implement both setup passes.

Test initial placements and starting resources.

## Step 10 — Normal turn state machine

Implement:

- pre-roll;
- roll;
- post-roll;
- end turn.

Initially support only EndTurn and dice/resource distribution.

Run complete games with dumb bots.

## Step 11 — Action generation

Implement:

- BuildRoad;
- BuildSettlement;
- BuildCity;
- BuyDevelopmentCard;
- Trade;
- development-card actions;
- EndTurn;
- Roll.

Ensure action generation is always legal.

## Step 12 — Building rules

Implement construction and graph connectivity.

Add longest-road calculation.

## Step 13 — Robber

Implement:

- 7 discard;
- robber movement;
- victim choice;
- RNG steal.

## Step 14 — Development cards

Implement one card at a time:

1. Knight
2. Road Building
3. Year of Plenty
4. Monopoly
5. Victory Point

Run tests after each.

## Step 15 — Trading

Implement bank trading first.

Then player trade:

- initial offer;
- response;
- counter;
- proposer resolution;
- atomic transaction.

Add extensive deterministic tests.

## Step 16 — Scoring and victory

Implement:

- victory points;
- Largest Army;
- Longest Road;
- winner detection.

## Step 17 — Timeout/error handling

Wrap every bot callback.

Test timeout, exceptions and invalid outputs.

## Step 18 — Replay

Verify complete game can produce a deterministic replay.

## Step 19 — Web integration

Expose:

- live events;
- public current state;
- replay package.

Then build/render the UI.

## Step 20 — End-to-end acceptance

Run:

- four trivial bots;
- mixed strategy bots;
- deterministic repeated runs;
- malformed/slow/exception bots;
- full-rule scenario tests.

Only after these pass should the implementation be considered complete.

## Implementation discipline

At each step:

1. write/modify code;
2. add tests;
3. run tests;
4. keep public contracts stable;
5. do not weaken hidden-information boundaries to simplify implementation.

If a later feature seems to require violating an earlier invariant, stop and refactor the internal implementation instead of changing the external contract.
