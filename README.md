# catan
Catan Simulator

## Platform demo

This repo includes a minimal platform adapter that runs the simulator, exposes replay/state endpoints, and streams live public events over WebSocket.

### Start the server
```powershell
python -m pip install -r requirements.txt
uvicorn src.platform.server:app --reload --port 8000
```

### Browser UI
Open http://localhost:8000/ui to view a mock board and event feed.

### API
- `POST /game/create?seed=42` creates a demo game and returns a `game_id`
- `GET /game/{game_id}/replay` returns replay metadata and ordered events
- `GET /game/{game_id}/state` returns a public summary, or `?player=P1` for per-player view
- `WS /ws/game/{game_id}` streams live events for the connected browser

### Example
```powershell
curl -X POST http://localhost:8000/game/create
curl http://localhost:8000/game/<game_id>/replay
```
