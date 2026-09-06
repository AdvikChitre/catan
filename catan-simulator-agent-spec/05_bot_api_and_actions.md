# 5. Bot API and Actions

## 5.1 Simulator calls bots

The simulator owns the game loop and calls bot methods.

Bots do not directly call simulator state-mutating methods.

## 5.2 Reference interface

Use this as the public contract. Names may be adapted to language conventions but signatures/semantics must remain equivalent.

```ts
interface CatanBot {
  onGameStart(view: GameView): void;

  chooseInitialPlacement(
    view: GameView,
    options: InitialPlacementOptions
  ): InitialPlacementAction;

  takeTurn(
    view: GameView,
    actions: readonly AvailableAction[]
  ): Action;

  createTradeOffer(
    view: GameView,
    context: TradeOfferContext
  ): TradeOffer;

  respondToTrade(
    view: GameView,
    offer: TradeOffer
  ): TradeResponse;

  chooseTradeOutcome(
    view: GameView,
    responses: readonly TradeResponse[]
  ): TradeResolution;

  chooseRobberAction(
    view: GameView,
    options: RobberOptions
  ): RobberAction;

  chooseRoadBuilding(
    view: GameView,
    options: RoadBuildingOptions
  ): RoadBuildingAction;

  chooseYearOfPlenty(
    view: GameView,
    options: YearOfPlentyOptions
  ): YearOfPlentyAction;

  chooseMonopoly(
    view: GameView,
    options: MonopolyOptions
  ): MonopolyAction;

  chooseDiscard(
    view: GameView,
    options: DiscardOptions
  ): DiscardAction;

  onEvent(event: GameEvent): void;

  onGameEnd(result: GameResult): void;
}
```

If a simpler generic request API is preferred internally, it is acceptable only if the external semantics remain the same and each decision context is explicit.

## 5.3 onGameStart

Called once after the bot is instantiated and the game has a valid initial view.

This method may initialize bot memory.

## 5.4 chooseInitialPlacement

Called during each setup placement.

The bot receives legal placement options.

Return exactly one legal placement.

## 5.5 takeTurn

Called whenever the active player must decide which current action to take.

The bot receives:

- current GameView;
- currently legal AvailableActions.

The bot returns one action.

## 5.6 AvailableAction union

At minimum:

```ts
type AvailableAction =
  | { type: "BUILD_ROAD"; edge: EdgeRef }
  | { type: "BUILD_SETTLEMENT"; vertex: VertexRef }
  | { type: "BUILD_CITY"; vertex: VertexRef }
  | { type: "BUY_DEVELOPMENT_CARD" }
  | { type: "PLAY_KNIGHT" }
  | { type: "PLAY_ROAD_BUILDING" }
  | { type: "PLAY_YEAR_OF_PLENTY" }
  | { type: "PLAY_MONOPOLY" }
  | { type: "TRADE" }
  | { type: "END_TURN" };
```

Victory Point cards are not an active action.

## 5.7 Action generation granularity

Concrete actions:

- roads;
- settlements;
- cities.

Umbrella actions:

- trade;
- complex development card operations.

The bot is not asked to choose between every possible trade as part of `AvailableActions`.

## 5.8 BuildRoad

```ts
{
  type: "BUILD_ROAD";
  edge: EdgeRef;
}
```

The referenced edge must be listed as a legal available action.

## 5.9 BuildSettlement

```ts
{
  type: "BUILD_SETTLEMENT";
  vertex: VertexRef;
}
```

## 5.10 BuildCity

```ts
{
  type: "BUILD_CITY";
  vertex: VertexRef;
}
```

## 5.11 BuyDevelopmentCard

No card identity is chosen by the bot.

The simulator draws the next card from the deck.

## 5.12 Trade

`TRADE` enters the trade interaction.

The simulator then calls:

```text
createTradeOffer
```

The bot returns:

```ts
interface TradeOffer {
  proposer: PlayerId;
  recipients: PlayerId[];
  give: ResourceCounts;
  receive: ResourceCounts;
}
```

The proposer is always the current player.

Recipients must be distinct opponents.

The offer must involve at least one resource given and one resource requested.

## 5.13 TradeResponse

```ts
type TradeResponse =
  | { type: "ACCEPT" }
  | { type: "REJECT" }
  | { type: "COUNTER_OFFER"; offer: TradeOffer };
```

Counter-offers must satisfy the same structural validity rules as ordinary offers.

## 5.14 TradeResolution

The initiating player chooses one final outcome from the collected responses.

Conceptually:

```ts
type TradeResolution =
  | { type: "ACCEPT_RESPONSE"; responder: PlayerId }
  | { type: "REJECT_ALL" };
```

If the chosen response is a counter-offer, the simulator executes the counter-offer against the initiating player subject to validity.

For deterministic ordering, responses are associated with player IDs and presented in player-order order.

## 5.15 RobberAction

```ts
interface RobberAction {
  tileId: TileId;
  victimPlayerId: PlayerId | null;
}
```

`victimPlayerId` is null only when there are no eligible victims.

The exact stolen resource is never chosen by the bot. The simulator chooses uniformly from the victim's resource cards using the seeded RNG.

## 5.16 RoadBuildingAction

```ts
interface RoadBuildingAction {
  firstRoad: EdgeRef;
  secondRoad: EdgeRef;
}
```

Validate sequentially because the first road can make the second road legal.

## 5.17 YearOfPlentyAction

Choose two resource cards subject to bank availability.

If bank availability prevents two requested cards, the action is invalid.

## 5.18 MonopolyAction

```ts
interface MonopolyAction {
  resourceType: ResourceType;
}
```

The simulator takes all cards of that resource from opponents and transfers them to the acting player.

## 5.19 DiscardAction

When required after a 7:

```ts
interface DiscardAction {
  resources: ResourceCounts;
}
```

The total discarded must be exactly floor(currentHandSize / 2).

## 5.20 EndTurn

```ts
{ type: "END_TURN" }
```

Ends the current normal action phase.

## 5.21 Action execution

All bot output is defensively validated even though AvailableActions were previously generated.

Invalid output must not mutate state.

The simulator should invoke the configured invalid-response policy (default: bot forfeits the game).
