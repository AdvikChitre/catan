# 1. System Architecture

```text
Browser
  | HTTP + WebSocket
  v
Web/API Server
  |---- Users
  |---- Bots / BotVersions
  |---- Rooms
  |---- Game metadata
  |
  v
Game Worker
  |---- Simulator
  |---- Bot adapters
           |
           v
       Bot Runners (4 isolated processes)
           |
           v
        User bot code

Game Worker -> event stream/replay -> Web/API -> Browser
```

## Components

### Web/API Server
Owns:
- authentication/session handling
- users
- bot CRUD
- room/lobby lifecycle
- game metadata
- replay metadata
- WebSocket subscriptions

It must not own live simulator state.

### Game Worker
Runs one or more games independently of the web server.
Owns the live simulator instance, connects four bot runners, publishes events, saves result/replay.

### Simulator
Owns authoritative Catan state and all Catan rules.
It does not know about users, rooms, uploads, HTML, or React.

### Bot Runner
Starts one selected immutable BotVersion in an isolated environment and speaks the canonical bot protocol.

### Database
Store users, bots, BotVersions, games, replay metadata.

### File/object storage
Store uploaded immutable bot artifacts and potentially replay/checkpoint files.

## Room vs Game
Room = lobby.
Game = one frozen match.
A Game references exact BotVersion IDs and a fixed seed.

Once a Game starts, room changes do not modify it.

## Dependency rule
Web UI -> API -> Game Service -> Game Worker -> Simulator/Bot Runner.
Simulator must remain independently runnable locally and in tests.
