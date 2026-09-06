# 7. Turn State Machine

## 7.1 Overview

The game must be implemented as an explicit state machine, not as one giant unstructured loop.

High-level states:

```text
SETUP_FORWARD
SETUP_REVERSE
PRE_ROLL
ROLL_REQUIRED
ROBBER_DISCARD
ROBBER_MOVE
ROBBER_STEAL
POST_ROLL
TRADE_NEGOTIATION
SPECIAL_ACTION
GAME_OVER
```

Internal sub-states may be added.

## 7.2 Game startup

1. Construct immutable BoardGeometry.
2. Create seeded RNG.
3. Create randomized BoardState.
4. Create BankState.
5. Create four PlayerStates.
6. Create TurnState.
7. Instantiate four bots.
8. Build first GameView for each player as needed.
9. Call `onGameStart`.
10. Publish `GameStarted`.
11. Enter setup.

## 7.3 Setup forward

Order:

```text
P1, P2, P3, P4
```

For each player:

1. calculate legal settlement vertices;
2. ask bot to choose initial placement;
3. validate settlement;
4. place settlement;
5. validate road connected to that settlement;
6. place road;
7. update pieces;
8. publish setup event.

## 7.4 Setup reverse

Order:

```text
P4, P3, P2, P1
```

Repeat placement.

After each player's second settlement, distribute starting resources from adjacent productive tiles.

## 7.5 First normal turn

Set:

```text
currentPlayer = P1
turnNumber = 1
phase = PRE_ROLL
```

Publish TurnStarted.

## 7.6 Pre-roll

Build GameView.

Calculate pre-roll actions.

Possible actions:

- Play Knight if available and allowed.
- Proceed to roll.
- The easiest API is to include an explicit `ROLL` control action in pre-roll.

Add:

```ts
{ type: "ROLL" }
```

to pre-roll action definitions even though it is not a normal post-roll action.

If the bot chooses Knight, execute it, then remain in PRE_ROLL.

If it chooses Roll, transition to ROLL_REQUIRED.

## 7.7 Roll

The simulator rolls both dice using seeded RNG.

Publish `DiceRolled`.

If total == 7:

```text
ROLL_REQUIRED
    -> ROBBER_DISCARD
```

Otherwise:

```text
ROLL_REQUIRED
    -> distribute resources
    -> POST_ROLL
```

## 7.8 Seven discard

Determine all players whose resource hand exceeds 7.

For each affected player, in deterministic player-id order:

1. build private GameView;
2. build DiscardOptions;
3. call `chooseDiscard`;
4. validate exact discard amount;
5. return cards to bank;
6. publish public discard event.

After all discards:

```text
-> ROBBER_MOVE
```

## 7.9 Robber move

Current player chooses destination tile from all legal tiles except the current robber tile.

If the destination has eligible victims, bot also chooses a victim.

If no eligible victim exists, victim is null.

Move robber and publish event.

If victim exists:

```text
-> ROBBER_STEAL
```

Otherwise:

```text
-> POST_ROLL
```

## 7.10 Robber steal

The simulator chooses one resource card uniformly from the victim's actual hand using seeded RNG.

Transfer exactly one card.

Publish appropriate public/private events.

Transition to POST_ROLL.

## 7.11 Post-roll

Repeatedly:

1. build fresh GameView;
2. calculate fresh AvailableActions;
3. call `takeTurn`;
4. execute action;
5. publish events;
6. check victory;
7. if not ended, repeat.

If bot chooses EndTurn:

```text
POST_ROLL -> TURN_END
```

## 7.12 Trade

When `TRADE` is selected:

1. call `createTradeOffer`;
2. validate offer;
3. publish TradeOfferCreated;
4. ask each recipient for a response in deterministic player-id order;
5. publish each response;
6. if counters exist, they are valid response candidates;
7. ask proposer to resolve;
8. execute at most one final transaction;
9. publish completion/failure;
10. return to POST_ROLL.

## 7.13 Special development-card action

For active cards:

```text
Play card
    -> mark card played
    -> perform card-specific decision(s)
    -> mutate state
    -> publish events
    -> return to POST_ROLL
```

## 7.14 Victory checking

After every state mutation that could affect scoring, check victory.

If a player reaches the victory threshold at a legal victory point moment, the game ends.

Publish:

```text
GameWon
GameEnded
```

Then call `onGameEnd` on all bots.

## 7.15 Turn end

After EndTurn:

1. publish TurnEnded;
2. check game not finished;
3. advance player clockwise;
4. increment turn number;
5. set phase to PRE_ROLL;
6. publish TurnStarted.
