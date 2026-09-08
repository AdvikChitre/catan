"""Minimal FastAPI adapter exposing simulator state, replay, and WebSocket event stream.

This is a development/demo adapter. It uses the existing `web_transport` helpers
and runs `Simulator` instances in background threads. Events are forwarded to
connected WebSocket clients.
"""
from __future__ import annotations

import atexit
import asyncio
import os
from typing import Dict, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel


class BotUploadRequest(BaseModel):
    bot_name: str
    bot_version: str
    entrypoint: str = "main.py"
    description: str = ""
    bot_code: str = ""
    use_sandbox: bool = False


# Get database URL from environment or use default
DATABASE_URL = os.getenv("CATAN_DB_URL", "sqlite:///catan_platform.db")

from ..simulation import Simulator
from ..web_transport.server import get_replay, get_state
from ..simulator.run import DummyBot
from ..simulator.types.identifiers import PlayerId
from .bot_runner import BotRunner
from .room_service import RoomService
from .ui import UI_HTML
from .bot_registry import BotRegistry
from .game_service import GameService


app = FastAPI()
room_service = RoomService(use_database=True, database_url=DATABASE_URL)
bot_registry = BotRegistry(use_database=True, database_url=DATABASE_URL)
game_service = GameService(use_database=True, database_url=DATABASE_URL)
_active_threads: Set[asyncio.Task] = set()


def _build_simulator(seed: int = 42, bot_map: Dict[PlayerId, object] | None = None) -> Simulator:
    sim = Simulator(seed=seed)
    if bot_map is None:
        bot_map = {
            PlayerId.P1: DummyBot(),
            PlayerId.P2: DummyBot(),
            PlayerId.P3: DummyBot(),
            PlayerId.P4: DummyBot(),
        }
    sim.register_bots(bot_map)
    return sim


# In-memory game registry for demo purposes: { game_id: {sim, thread, subscribers:set} }
games: Dict[str, Dict] = {}


def _start_simulator_task(sim: Simulator, game_id: str):
    """Start simulator.run() as an asyncio task on the current event loop."""

    async def broadcast(event):
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

    async def broadcast_type_completion(gid: str):
        subs = games[gid]["subscribers"].copy()
        payload = {"type": "SIMULATOR_COMPLETED", "game_id": gid}
        for ws in list(subs):
            try:
                await ws.send_json(payload)
            except Exception:
                pass

    async def runner():
        try:
            sim.run()
        finally:
            await broadcast_type_completion(game_id)
            games[game_id]["task"] = None
            _active_threads.discard(task)

    def on_event(event):
        asyncio.create_task(broadcast(event))

    sim.event_bus.subscribe(on_event, player_id=None)
    task = asyncio.create_task(runner())
    games[game_id]["task"] = task
    _active_threads.add(task)
    return task


def _ensure_unique_game_id(base_game_id: str) -> str:
    """Return a unique game id for the platform even when the simulator seed repeats."""
    if base_game_id not in games:
        return base_game_id
    suffix = 2
    candidate = f"{base_game_id}-{suffix}"
    while candidate in games:
        suffix += 1
        candidate = f"{base_game_id}-{suffix}"
    return candidate


@app.post("/game/create")
async def create_game(seed: int = 42):
    """Create and start a simulator instance for development/demo.

    Returns the `game_id` which can be used to query state/replay or connect via WebSocket.
    """
    sim = _build_simulator(seed=seed)
    base_game_id = sim.game_state.game_id
    game_id = _ensure_unique_game_id(base_game_id)
    if game_id != base_game_id:
        sim.game_state.game_id = game_id
        sim.replay_recorder.metadata["game_id"] = game_id
    if game_id in games:
        raise HTTPException(status_code=400, detail="Game already exists")

    game_service.create_game(game_id, seed=seed, players=[p.value for p in PlayerId.all_players()])
    games[game_id] = {"sim": sim, "subscribers": set(), "task": None}
    _start_simulator_task(sim, game_id)
    return {"game_id": game_id}


@app.get("/games")
async def list_games():
    return {"games": [game.to_dict() for game in game_service.list_games()]}


@app.get("/games/{game_id}")
async def get_game_metadata(game_id: str):
    game = game_service.get_game(game_id)
    if game is None:
        raise HTTPException(status_code=404, detail="Game not found")
    return game.to_dict()


@app.post("/rooms")
async def create_room(room_name: str = "Demo Room", created_by: str = "player-1"):
    room = room_service.create_room(room_name, created_by)
    return {"room": {"room_id": room.room_id, "name": room.name, "created_by": room.created_by, "seats": [
        {"player_name": seat.player_name, "ready": seat.ready} for seat in room.seats
    ]}}


@app.post("/rooms/{room_id}/join")
async def join_room(room_id: str, player_name: str):
    room = room_service.join_room(room_id, player_name)
    return {"room_id": room.room_id, "player_name": player_name, "seats": [
        {"player_name": seat.player_name, "ready": seat.ready} for seat in room.seats
    ]}


@app.post("/rooms/{room_id}/ready")
async def set_room_ready(room_id: str, player_name: str, ready: bool = True):
    room = room_service.set_ready(room_id, player_name, ready)
    return {"room_id": room.room_id, "player_name": player_name, "ready": ready}


@app.post("/rooms/{room_id}/attach-bot")
async def attach_bot(room_id: str, player_name: str, bot_name: str = "demo-bot", bot_version: str = "v1"):
    room = room_service.get_room(room_id)
    
    # Check if this is a registered bot
    bot_id = f"{bot_name}-{bot_version}"
    registered_bot = bot_registry.get_bot(bot_id)
    
    if registered_bot and registered_bot.use_sandbox and registered_bot.bot_code:
        # Use sandboxed runner
        bot = BotRunner(
            bot_id=f"{player_name}-{bot_name}",
            name=bot_name,
            version=bot_version,
            use_sandbox=True,
            bot_code=registered_bot.bot_code,
            sandbox_config=registered_bot.sandbox_config
        )
    else:
        # Use regular runner
        bot = BotRunner(bot_id=f"{player_name}-{bot_name}", name=bot_name, version=bot_version)
    
    bot.validate()
    room_service.attach_bot(room_id, player_name, bot)
    return {"room_id": room_id, "player_name": player_name, "bot_id": bot.bot_id, "status": bot.status}


@app.post("/rooms/{room_id}/start-game")
async def start_room_game(room_id: str, seed: int = 42):
    room = room_service.get_room(room_id)
    if not room_service.can_start_game(room_id):
        raise HTTPException(status_code=400, detail="Room is not ready to start")

    player_mapping: Dict[PlayerId, object] = {}
    players = []
    for idx, seat in enumerate(room.seats):
        if seat.player_name is None:
            continue
        players.append(seat.player_name)
        player_id = PlayerId.all_players()[idx]
        
        # Handle bot_runner - could be BotRunner object or string (bot_id)
        if seat.bot_runner is not None:
            if isinstance(seat.bot_runner, str):
                # Convert bot_id string back to BotRunner by looking up in registry
                registered_bot = bot_registry.get_bot(seat.bot_runner)
                if registered_bot and registered_bot.use_sandbox and registered_bot.bot_code:
                    # Reconstruct sandboxed runner
                    bot = BotRunner(
                        bot_id=registered_bot.bot_id,
                        name=registered_bot.name,
                        version=registered_bot.version,
                        use_sandbox=True,
                        bot_code=registered_bot.bot_code,
                        sandbox_config=registered_bot.sandbox_config
                    )
                    bot.validate()
                    player_mapping[player_id] = bot
                else:
                    # Fallback to DummyBot
                    player_mapping[player_id] = DummyBot()
            elif hasattr(seat.bot_runner, 'take_turn'):
                # It's already a proper BotRunner object
                player_mapping[player_id] = seat.bot_runner
            else:
                player_mapping[player_id] = DummyBot()
        else:
            player_mapping[player_id] = DummyBot()

    sim = _build_simulator(seed=seed, bot_map=player_mapping)
    base_game_id = sim.game_state.game_id
    game_id = _ensure_unique_game_id(base_game_id)
    if game_id != base_game_id:
        sim.game_state.game_id = game_id
        sim.replay_recorder.metadata["game_id"] = game_id
    game_service.create_game(game_id, room_id=room_id, seed=seed, players=players)
    games[game_id] = {"sim": sim, "subscribers": set(), "task": None}
    _start_simulator_task(sim, game_id)
    room.status = "playing"
    return {"game_id": game_id, "room_id": room_id}


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


@app.get("/bots")
async def list_bots():
    return {"bots": bot_registry.list_bots()}


@app.post("/bots/upload")
async def upload_bot(request: BotUploadRequest):
    from .sandbox import SandboxConfig
    
    sandbox_config = SandboxConfig() if request.use_sandbox else None
    package = bot_registry.register(
        request.bot_name,
        request.bot_version,
        entrypoint=request.entrypoint,
        description=request.description,
        bot_code=request.bot_code if request.use_sandbox else None,
        use_sandbox=request.use_sandbox,
        sandbox_config=sandbox_config
    )
    return {
        "bot_id": package.bot_id,
        "name": package.name,
        "version": package.version,
        "entrypoint": package.entrypoint,
        "validated": package.validated,
        "validation_errors": package.validation_errors,
        "use_sandbox": package.use_sandbox,
    }


@app.get("/bots/{bot_id}")
async def get_bot(bot_id: str):
    package = bot_registry.get_bot(bot_id)
    if package is None:
        raise HTTPException(status_code=404, detail="Bot not found")
    return {
        "bot_id": package.bot_id,
        "name": package.name,
        "version": package.version,
        "entrypoint": package.entrypoint,
        "description": package.description,
        "validated": package.validated,
        "validation_errors": package.validation_errors,
    }


def _shutdown_active_threads() -> None:
    """Ensure all simulator worker threads exit before interpreter shutdown."""
    for task in list(_active_threads):
        if not task.done():
            task.cancel()
    _active_threads.clear()


atexit.register(_shutdown_active_threads)
