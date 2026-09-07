"""Minimal FastAPI adapter exposing simulator state, replay, and WebSocket event stream.

This is a development/demo adapter. It uses the existing `web_transport` helpers
and runs `Simulator` instances in background threads. Events are forwarded to
connected WebSocket clients.
"""
from __future__ import annotations

import asyncio
import threading
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse

from ..simulation import Simulator
from ..web_transport.server import get_replay, get_state
from ..simulator.run import DummyBot
from ..simulator.types.identifiers import PlayerId
from .ui import UI_HTML


app = FastAPI()

# In-memory game registry for demo purposes: { game_id: {sim, thread, subscribers:set} }
games: Dict[str, Dict] = {}


def _start_simulator_in_thread(sim: Simulator, loop: asyncio.AbstractEventLoop, game_id: str) -> threading.Thread:
    """Start simulator.run() in a background thread and forward events to the ASGI loop.

    The simulator's EventBus will call the subscribed callback from the simulator thread;
    the callback uses `loop.call_soon_threadsafe` to schedule async broadcasts.
    """

    async def broadcast(event):
        # runs in the event loop
        subs: Set[WebSocket] = games[game_id]["subscribers"].copy()
        payload = {
            "sequence": event.sequence_number,
            "type": event.event_type,
            "game_id": event.game_id,
            "turn_number": event.turn_number,
            "player_id": event.player_id.value if event.player_id else None,
            "visibility": event.visibility,
            "data": event.data,
        }
        for ws in list(subs):
            try:
                await ws.send_json(payload)
            except Exception:
                try:
                    await ws.close()
                except Exception:
                    pass
                games[game_id]["subscribers"].discard(ws)

    def on_event(event):
        # schedule broadcast in the asyncio event loop
        try:
            if loop.is_running():
                asyncio.run_coroutine_threadsafe(broadcast(event), loop)
        except RuntimeError:
            # loop closed or unavailable
            pass

    sim.event_bus.subscribe(on_event, player_id=None)

    def runner():
        try:
            sim.run()
        finally:
            # notify clients that the simulator finished
            try:
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(broadcast_type_completion(game_id), loop)
            except Exception:
                pass

    def start_thread():
        t = threading.Thread(target=runner, daemon=True)
        t.start()
        return t

    async def broadcast_type_completion(gid: str):
        subs = games[gid]["subscribers"].copy()
        payload = {"type": "SIMULATOR_COMPLETED", "game_id": gid}
        for ws in list(subs):
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    return start_thread()


@app.post("/game/create")
async def create_game(seed: int = 42):
    """Create and start a simulator instance for development/demo.

    Returns the `game_id` which can be used to query state/replay or connect via WebSocket.
    """
    sim = Simulator(seed=seed)
    # register four DummyBots for now
    bots = {
        PlayerId.P1: DummyBot(),
        PlayerId.P2: DummyBot(),
        PlayerId.P3: DummyBot(),
        PlayerId.P4: DummyBot(),
    }
    sim.register_bots(bots)

    game_id = sim.game_state.game_id
    if game_id in games:
        raise HTTPException(status_code=400, detail="Game already exists")

    loop = asyncio.get_event_loop()

    games[game_id] = {"sim": sim, "subscribers": set(), "thread": None}
    t = _start_simulator_in_thread(sim, loop, game_id)
    games[game_id]["thread"] = t

    return {"game_id": game_id}


@app.get("/game/{game_id}/replay")
async def replay(game_id: str):
    info = games.get(game_id)
    if not info:
        raise HTTPException(status_code=404, detail="Game not found")
    sim: Simulator = info["sim"]
    return get_replay(sim)


@app.get("/game/{game_id}/state")
async def state(game_id: str, player: str | None = None):
    info = games.get(game_id)
    if not info:
        raise HTTPException(status_code=404, detail="Game not found")
    sim: Simulator = info["sim"]
    if player is None:
        return get_state(sim, None)
    try:
        pid = PlayerId[player]
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid player id")
    return get_state(sim, pid)


@app.websocket("/ws/game/{game_id}")
async def websocket_endpoint(websocket: WebSocket, game_id: str):
    await websocket.accept()
    info = games.get(game_id)
    if not info:
        await websocket.send_json({"error": "game-not-found"})
        await websocket.close()
        return
    info["subscribers"].add(websocket)
    try:
        # keep the connection open; the broadcast coroutine will push events
        while True:
            # accept pings from client to keep connection alive; don't expect messages
            try:
                msg = await websocket.receive_text()
            except WebSocketDisconnect:
                break
    finally:
        info["subscribers"].discard(websocket)


@app.get("/")
async def index():
    return HTMLResponse(UI_HTML)


@app.get("/ui")
async def ui_page():
    return HTMLResponse(UI_HTML)
