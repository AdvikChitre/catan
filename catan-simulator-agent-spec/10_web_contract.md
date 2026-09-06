# 10. Web Contract

## 10.1 Separation

The simulator core must not depend on React, browser APIs, DOM APIs, or rendering.

The web application consumes simulator output.

## 10.2 Live mode

A web client should be able to receive:

- game metadata;
- current public board state;
- public events as they happen;
- final result.

A WebSocket or Server-Sent Events transport is acceptable.

Prefer WebSocket if bidirectional control/inspection will be useful later.

## 10.3 Replay mode

The web client should be able to load a replay object containing:

```text
game metadata
initial board
ordered events
final result
```

and reconstruct the visual timeline.

## 10.4 Public spectator state

The default spectator view may contain public game state.

It must not expose private player resources or private development-card identities.

## 10.5 Event serialization

Use JSON-compatible DTOs.

Do not serialize class instances with private runtime state.

Example:

```json
{
  "sequence": 42,
  "gameId": "game-183",
  "turnNumber": 12,
  "type": "RoadBuilt",
  "visibility": { "type": "PUBLIC" },
  "payload": {
    "playerId": "P2",
    "edge": {
      "vertexA": { "x": 3, "y": 2 },
      "vertexB": { "x": 4, "y": 2 }
    }
  }
}
```

## 10.6 Current-state endpoint/message

Provide a public/spectator current state representation that is independent of bot-private GameView.

The UI does not need access to the bot's private view.

## 10.7 Renderer responsibilities

Renderer handles:

- visual board layout;
- pieces;
- robber;
- dice;
- player panels;
- trade messages;
- development-card events;
- replay controls.

Renderer must not implement game rules as its own source of truth.
