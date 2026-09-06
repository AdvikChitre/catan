# 1. Scope and Architecture

## 1.1 Required component model

Implement the simulator using these responsibilities:

```text
Simulator
├── GameState
├── BoardGeometry
├── RulesEngine
├── ActionGenerator
├── GameViewBuilder
├── TurnManager / state machine
├── Bank
├── EventBus
├── SeededRng
├── BotManager
└── ReplayRecorder
```

The exact class names may differ only if behaviour and responsibilities remain equivalent.

## 1.2 Simulator

The Simulator is the top-level orchestrator.

Responsibilities:

- own the four bot instances;
- own authoritative GameState;
- own BoardGeometry;
- own RNG;
- initialize the game;
- execute setup;
- execute turns;
- ask bots for decisions;
- execute valid decisions;
- publish events;
- check victory;
- terminate the game;
- expose replay data.

The Simulator must not contain strategic decisions.

## 1.3 GameState

GameState is the complete mutable truth of one running game.

Recommended shape:

```ts
interface GameState {
  gameId: string;
  seed: number | string;

  board: BoardState;
  bank: BankState;
  players: PlayerState[];
  turn: TurnState;

  phase: GamePhase;
  status: GameStatus;
}
```

GameState may contain internal/private fields that are never exposed to bots.

## 1.4 BoardGeometry

Immutable topology of the canonical Catan board.

It defines:

- all vertices;
- all edges;
- all tiles;
- adjacency relationships;
- ports.

It does NOT contain mutable gameplay state.

## 1.5 BoardState

Mutable board information:

- randomized tile contents;
- robber position;
- building occupancy;
- road ownership.

## 1.6 RulesEngine

RulesEngine answers questions and calculates derived information.

It must not become the owner of mutable global state.

Typical operations:

```text
getLegalRoadPlacements
getLegalSettlementPlacements
getLegalCityPlacements
canBuyDevelopmentCard
canPlayDevelopmentCard
getEligibleRobberVictims
getProduction
calculateLongestRoad
calculateVictoryPoints
calculateLargestArmy
hasWinner
```

## 1.7 ActionGenerator

ActionGenerator converts current state into legal choices for the requested bot.

Example:

```ts
getAvailableActions(state, playerId, phase): AvailableAction[]
```

It must never include an action that is currently illegal.

For actions with a large/contextual parameter space, use umbrella actions such as `TRADE` instead of enumerating every possible trade.

## 1.8 GameViewBuilder

Build a fresh player-specific immutable view every time a bot is asked for a decision.

Inputs:

```text
GameState
playerId
```

Output:

```text
GameView
```

It must filter hidden information correctly.

## 1.9 Bank

Bank is a stateful subsystem or service responsible for:

- resource pool counts;
- development-card deck;
- transfers between bank and players.

Bots never see the Bank.

All transfers should go through one centralized interface so invariants are easy to enforce.

## 1.10 EventBus

EventBus delivers GameEvent values to:

- relevant bots;
- ReplayRecorder;
- optional simulator observers.

EventBus must preserve deterministic sequence ordering.

Bot event delivery must happen after the corresponding authoritative state mutation.

## 1.11 BotManager

BotManager creates exactly four bot instances and associates each with one PlayerId.

The simulator calls methods on these objects.

A bot object may store arbitrary internal state for the duration of a game.

## 1.12 ReplayRecorder

Record:

- game metadata;
- seed;
- initial board;
- ordered events;
- final result.

Replay output must be sufficient for the web client to visualize the game and for a deterministic rerun to be identified.

## 1.13 No direct bot-to-simulator calls

Do NOT expose:

```ts
bot.simulator
bot.gameState
bot.bank
bot.otherPlayers
```

Do NOT implement:

```ts
bot.buildRoad(...)
simulator.buildRoad(...)
```

as bot-facing direct mutation APIs.

Instead:

```text
Simulator -> bot.TakeTurn(view, availableActions)
Bot -> returns Action
Simulator -> executes Action
```
