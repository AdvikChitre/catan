# 4. GameView and Visibility

## Rule
Bots receive a fresh read-only GameView for themselves at every decision.

## GameView
```ts
interface GameView {
  gameId: string;
  self: SelfView;
  board: BoardView;
  opponents: OpponentView[];
  turn: TurnView;
}
```

## SelfView
Includes:
- playerId
- own resources
- own development cards
- remaining pieces
- Knights played
- own VP
- Longest Road/Largest Army flags

## OpponentView
Includes only public state:
- playerId
- visible roads
- visible buildings
- Knights played
- public/visible VP and achievements

Never include opponent resources or development-card hands.

## BoardView
Includes public:
- tiles
- number tokens
- robber
- roads
- settlements/cities
- ports

## No event history
GameView does not contain the event log.

Bots learn history only through real-time OnEvent and their own memory.

## Immutability
Bot code must not be able to mutate simulator state through a GameView.

## Replay privacy
Historical replay shows only what was knowable at the selected point.
A later revelation must not appear when scrubbing backward.
