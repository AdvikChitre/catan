# 6. Events

## 6.1 Event purpose

Events serve two roles:

1. real-time information to bots through `onEvent`;
2. deterministic replay data for the visualizer.

Events are not a substitute for current game state.

## 6.2 Event base shape

Recommended:

```ts
interface GameEventBase {
  sequence: number;
  gameId: string;
  turnNumber: number;
  type: string;
  visibility: EventVisibility;
}
```

The sequence number is the authoritative event ordering mechanism.

## 6.3 Visibility

At minimum:

```ts
type EventVisibility =
  | { type: "PUBLIC" }
  | { type: "PLAYER_ONLY"; playerId: PlayerId }
  | { type: "PLAYERS"; playerIds: PlayerId[] };
```

Use the least-private visibility that is correct.

## 6.4 Required event types

Implement at least:

```text
GameStarted
SetupPlacementMade
TurnStarted
DiceRolled
ResourcesReceived
ResourcesDiscarded
RoadBuilt
SettlementBuilt
CityBuilt
DevelopmentCardPurchased
DevelopmentCardPlayed
RobberMoved
ResourceStolen
TradeOfferCreated
TradeResponseReceived
TradeCounterOfferCreated
TradeCompleted
TradeFailed
TurnEnded
LongestRoadChanged
LargestArmyChanged
GameWon
GameEnded
```

Additional events may be added if useful.

## 6.5 DiceRolled

Public payload:

```ts
{
  type: "DiceRolled";
  playerId: PlayerId;
  die1: number;
  die2: number;
  total: number;
}
```

## 6.6 ResourcesReceived

Public because players can observe who receives cards from a roll.

Payload:

```ts
{
  type: "ResourcesReceived";
  playerId: PlayerId;
  resources: ResourceCounts;
}
```

Do not expose a player's pre-existing resource hand or total hand size unless publicly observable by the rules.

## 6.7 ResourcesDiscarded

Do not reveal which resource types a player discarded.

Use:

```ts
{
  type: "ResourcesDiscarded";
  playerId: PlayerId;
  count: number;
}
```

The affected player knows its own discard from its private decision state.

## 6.8 DevelopmentCardPurchased

Public:

```ts
{
  type: "DevelopmentCardPurchased";
  playerId: PlayerId;
}
```

Do not reveal the card type.

## 6.9 DevelopmentCardPlayed

The type is public because playing a development card is public.

For Victory Point cards, no active play event is generated because the card remains hidden until the victory/scoring rule requires disclosure.

## 6.10 TradeOfferCreated

Include the actual offer contents.

Example:

```ts
{
  type: "TradeOfferCreated";
  offer: TradeOffer;
}
```

Recipients and spectators see the offer because it is a table-visible proposal under this simulator model.

## 6.11 Trade response events

Record:

- who responded;
- whether accept/reject;
- counter-offer details if countered.

## 6.12 TradeCompleted

Record:

```ts
{
  proposer: PlayerId;
  responder: PlayerId;
  give: ResourceCounts;
  receive: ResourceCounts;
}
```

## 6.13 ResourceStolen

Do NOT reveal the stolen resource type to other players.

Use:

```ts
{
  thief: PlayerId;
  victim: PlayerId;
}
```

The victim and thief may receive a more detailed private event if desired, but public replay must not reveal hidden information.

For the simplest deterministic design, use a public event for thief/victim and a private event to thief/victim containing resource type.

## 6.14 Event delivery ordering

For every mutation:

1. mutate authoritative state;
2. create event(s);
3. assign deterministic sequence numbers;
4. record event;
5. deliver to eligible bots;
6. continue game flow.

This guarantees bots observe events after the corresponding state change.

## 6.15 Bot OnEvent semantics

Every bot receives only events visible to that player.

Bots may:

- ignore events;
- update internal state;
- keep a history;
- maintain estimators.

The simulator must not assume any bot remembers anything.

## 6.16 Event history storage

ReplayRecorder stores all events.

Bots do NOT receive replay history automatically.
