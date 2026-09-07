# Platform Integration Implementation Plan

This document outlines the architecture, integration contract, milestones, and initial implementation steps
to attach the existing simulator to a platform backend and Web UI.

## Goals
- Expose simulator gameplay and replay data via HTTP and WebSocket for a browser UI.
- Keep the simulator independent and testable locally.
- Provide an adapter layer (Game Worker) to run games, manage bot runners, and publish events.

## Architecture (high level)

Browser <-> Web/API Server <-> Game Worker (runs `Simulator`) -> Event stream / Replay storage

- Web/API Server: user, bot, room CRUD, auth, WebSocket subscriptions (stateless relative to live simulator state).
- Game Worker: owns `Simulator`, `BotRunner` adapters, publishes `GameEvent` via `EventBus`, stores replay via `ReplayRecorder`.
- Storage: DB for users/bots/versions and object store for uploaded artifacts and replays.

## Integration contract (based on `catan-simulator-agent-spec`)
- Transport: JSON over HTTP + WebSocket (prefer WebSocket for bidirectional and live event stream).
- Replay endpoint: JSON object with `metadata` and `events` (sequence, type, game_id, turn_number, player_id, visibility, data).
- State endpoint: public summary or per-player `GameView` snapshot (use `web_transport.get_state`).
- Events: JSON-serializable DTOs only; do not expose internal object instances.

## Milestones
1. Read and align with simulator and web contract (completed).
2. Design API endpoints and WebSocket message shapes (this document).
3. Scaffold minimal platform adapter (HTTP replay/state + WebSocket event stream). (scaffolded)
4. Add BotRunner integration and secure isolated execution for uploaded bot artifacts.
5. Implement lobby/room lifecycle and game creation APIs.
6. Implement frontend MVP for live game and replay visualization.
7. Add CI tests, integration tests, and deployment instructions.

## Initial Implementation Tasks (MVP)
1. Provide `GET /game/{id}/replay` using `web_transport.get_replay(sim)`.
2. Provide `GET /game/{id}/state` using `web_transport.get_state(sim, player_id)`.
3. Provide `WS /ws/game/{id}` that streams serialized `GameEvent` objects in order.
4. Provide a `POST /game/create` or `/game/{id}/start` helper for local development to start a `Simulator` instance and register test/dummy bots.

## Tech choices and notes
- Use the existing `src/web_transport` helpers to keep the simulator core dependency-free.
- For the example adapter we use `FastAPI` + `uvicorn` for rapid development, but the `web_transport` helpers are framework-independent and can be wrapped in Flask, Django, or ASGI frameworks.
- Ensure thread/async handoff between a blocking simulator and async WebSocket loop using `asyncio` queues and `loop.call_soon_threadsafe`.

## Next steps
- Implement a minimal server adapter in `src/platform/server.py` that demonstrates the above endpoints and WebSocket streaming.
- Create a small example web UI (static or React) to consume the WebSocket and render events.

---
Generated from repository inspection and simulator/web contract documentation.
