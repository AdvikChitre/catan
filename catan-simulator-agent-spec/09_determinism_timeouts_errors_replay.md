# 9. Determinism, Timeouts, Errors, Replay

## 9.1 Seeded RNG

Create one RNG instance per game from the game seed.

All random operations must consume RNG from that instance.

Do not use implicit randomness elsewhere.

## 9.2 Random operations

The seeded RNG controls:

- tile/resource randomization;
- development deck shuffle;
- dice;
- robber steals;
- any other game randomness.

## 9.3 Decision timeout

Maximum wall-clock time per bot decision: 3 seconds.

Apply this to every bot callback:

- onGameStart if considered a decision boundary;
- chooseInitialPlacement;
- takeTurn;
- createTradeOffer;
- respondToTrade;
- chooseTradeOutcome;
- chooseRobberAction;
- chooseRoadBuilding;
- chooseYearOfPlenty;
- chooseMonopoly;
- chooseDiscard.

The competition runner may choose not to count lifecycle callbacks like onGameEnd toward the 3-second gameplay budget; gameplay decisions must always be bounded.

On timeout, default policy:

```text
bot forfeits game
game ends
record BotTimeout event/error
```

Do not wait indefinitely.

## 9.4 Bot exceptions

If a bot callback throws:

1. catch the exception at the simulator boundary;
2. record an error with player ID, method name and turn;
3. terminate the game with that bot forfeiting.

Do not allow an exception to partially mutate simulator state.

## 9.5 Invalid bot response

If a response:

- is malformed;
- references an unavailable action;
- violates a decision-specific constraint;
- contains invalid quantities;

then:

1. do not mutate state;
2. record invalid-response error;
3. forfeit the bot/game by default.

This avoids complicated retry semantics and keeps tournament outcomes deterministic.

## 9.6 Deterministic player ordering

Whenever multiple players must be processed without a natural game order, use:

```text
P1, P2, P3, P4
```

or the current canonical player order.

Do not depend on object insertion order.

## 9.7 Logical event sequence

Every event gets an incrementing integer:

```text
1, 2, 3, ...
```

No event may share a sequence number.

Sequence order is the authoritative game chronology.

## 9.8 Game result

Recommended:

```ts
interface GameResult {
  gameId: string;
  seed: string | number;
  winner: PlayerId | null;

  finalVictoryPoints: Record<PlayerId, number>;

  turnCount: number;

  termination:
    | "NORMAL_VICTORY"
    | "BOT_TIMEOUT"
    | "BOT_EXCEPTION"
    | "BOT_INVALID_RESPONSE"
    | "SIMULATOR_ERROR";
}
```

## 9.9 Replay package

Minimum replay data:

```text
game metadata
seed
bot identifiers/names
initial board configuration
ordered public event stream
final result
```

Private event payloads may be stored for authorized local debugging, but the default web replay must not expose hidden information before it should be revealed.

## 9.10 Replay determinism test

Running the same game configuration and seed twice must produce byte-equivalent normalized event streams and identical final results.

If event timestamps are included for diagnostics, do not compare those wall-clock values.

Use logical sequence and deterministic payloads for replay comparison.
