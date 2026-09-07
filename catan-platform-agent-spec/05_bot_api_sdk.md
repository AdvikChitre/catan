# 5. Bot API and SDK

Every user bot implements the canonical CatanBot interface.

Reference semantics:

```ts
interface CatanBot {
  onGameStart(view: GameView): void;
  chooseInitialPlacement(view: GameView, options: InitialPlacementOptions): InitialPlacementAction;
  takeTurn(view: GameView, actions: readonly AvailableAction[]): Action;

  createTradeOffer(view: GameView, context: TradeOfferContext): TradeOffer;
  respondToTrade(view: GameView, offer: TradeOffer): TradeResponse;
  chooseTradeOutcome(view: GameView, responses: readonly TradeResponse[]): TradeResolution;

  chooseRobberAction(view: GameView, options: RobberOptions): RobberAction;
  chooseRoadBuilding(view: GameView, options: RoadBuildingOptions): RoadBuildingAction;
  chooseYearOfPlenty(view: GameView, options: YearOfPlentyOptions): YearOfPlentyAction;
  chooseMonopoly(view: GameView, options: MonopolyOptions): MonopolyAction;
  chooseDiscard(view: GameView, options: DiscardOptions): DiscardAction;

  onEvent(event: GameEvent): void;
  onGameEnd(result: GameResult): void;
}
```

## AvailableAction
```ts
type AvailableAction =
  | { type: "ROLL" }
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

VP cards are not active actions.

## Trade
```ts
interface TradeOffer {
  proposer: PlayerId;
  recipients: PlayerId[];
  give: ResourceCounts;
  receive: ResourceCounts;
}
```

Response:
```ts
type TradeResponse =
  | { type: "ACCEPT" }
  | { type: "REJECT" }
  | { type: "COUNTER_OFFER"; offer: TradeOffer };
```

## SDK template
Provide a downloadable package with:
- bot entrypoint
- SDK types
- simple example bot
- README
- local runner/tests

The example bot must demonstrate:
- TakeTurn
- OnEvent
- private memory
- trade response
- returning legal actions

## Versioning
Bots declare SDK/protocol version.
Uploaded versions are immutable.
A Game freezes exact BotVersion IDs.

## Local compatibility
The same bot package/API should work against a local simulator harness and the hosted runner.
