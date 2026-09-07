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

### Bot registry

The platform includes a lightweight in-memory bot registry for uploaded bot versions.

- `GET /bots` lists all registered bot versions
- `POST /bots/upload?bot_name=alpha&bot_version=v1&entrypoint=main.py` creates and validates a bot package
- `GET /bots/{bot_id}` fetches a specific version

Example:
```powershell
curl "http://localhost:8000/bots/upload?bot_name=alpha&bot_version=v1&entrypoint=main.py&description=first+bot"
```
