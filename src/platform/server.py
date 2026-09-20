"""Local replay-first platform: submit, simulate in a worker, watch later."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import logging
import os
from pathlib import Path
import threading
import uuid

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ..simulator.run import DummyBot
from ..simulator.types.identifiers import PlayerId
from .bot_registry import BotRegistry
from .bot_runner import BotRunner
from .recording import RecordingSimulator
from .replay_store import ReplayStore
from .room_service import RoomService
from .sandbox import SandboxConfig

DATABASE_URL = os.getenv("CATAN_DB_URL", "sqlite:///catan_platform.db")
default_replays = (DATABASE_URL.removeprefix("sqlite:///") + ".replays"
                   if DATABASE_URL.startswith("sqlite:///") else "catan_replays")
store = ReplayStore(os.getenv("CATAN_REPLAY_DIR", default_replays))
store.recover()
room_service = RoomService(use_database=True, database_url=DATABASE_URL)
bot_registry = BotRegistry(use_database=True, database_url=DATABASE_URL)
for _old_game in store.list_games():
    if _old_game.get("room_id") and _old_game["status"] not in ("queued", "running"):
        room_service.room_repository.update_room_status(_old_game["room_id"], "finished")
workers = ThreadPoolExecutor(max_workers=2, thread_name_prefix="catan-match")
mutation_lock = threading.RLock()
app = FastAPI(title="Catan replay studio")
assets = Path(__file__).with_name("static")
app.mount("/static", StaticFiles(directory=assets, check_dir=False), name="static")


class BotUploadRequest(BaseModel):
    bot_name: str = Field(max_length=80)
    bot_version: str = Field(max_length=40)
    entrypoint: str = Field(default="main.py", max_length=120)
    description: str = Field(default="", max_length=2000)
    bot_code: str = Field(default="", max_length=200_000)
    use_sandbox: bool = False


class RoomJoinRequest(BaseModel):
    player_name: str = Field(min_length=1, max_length=80)


class RoomReadyRequest(RoomJoinRequest):
    ready: bool = True


class AttachBotRequest(RoomJoinRequest):
    bot_name: str
    bot_version: str = "v1"


class StartGameRequest(BaseModel):
    seed: int = Field(default=42, ge=0, le=2**31 - 1)


@app.exception_handler(KeyError)
async def missing(request: Request, error: KeyError):
    return JSONResponse(status_code=404, content={"detail": "The requested item was not found."})


@app.exception_handler(ValueError)
async def invalid(request: Request, error: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(error)})


def now():
    return datetime.now(timezone.utc).isoformat()


def package_data(package):
    return {"bot_id": package.bot_id, "name": package.name, "version": package.version,
            "entrypoint": package.entrypoint, "description": package.description,
            "validated": package.validated, "validation_errors": package.validation_errors,
            "use_sandbox": package.use_sandbox}


def require_bot(bot_id):
    package = bot_registry.get_bot(bot_id) if bot_id else None
    if package is None or not package.validated:
        raise ValueError("Select an existing, valid bot version")
    return package


def _run_match(metadata, packages):
    sim = None
    runners = []
    try:
        metadata.update(status="running", started_at=now())
        store.save_metadata(metadata)
        sim = RecordingSimulator(seed=metadata["seed"])
        sim.game_state.game_id = metadata["game_id"]
        sim.replay_recorder.metadata["game_id"] = metadata["game_id"]
        bot_map = {}
        for pid, package in zip(PlayerId.all_players(), packages):
            if package is None:
                bot_map[pid] = DummyBot()
            else:
                runner = BotRunner(bot_id=package.bot_id, name=package.name, version=package.version,
                                   use_sandbox=package.use_sandbox, bot_code=package.bot_code,
                                   sandbox_config=SandboxConfig(wall_time_limit=0.8))
                if not runner.validate().get("ok"):
                    raise ValueError("A selected bot failed validation")
                runners.append(runner)
                bot_map[pid] = runner
        sim.register_bots(bot_map)
        sim.begin_recording()
        sim.run()
        recording = sim.export_recording(dict(metadata))
        metadata.update(status=recording["result"]["status"], finished_at=now(),
                        winner=recording["result"]["winner"], reason=recording["result"]["reason"],
                        replay_available=True)
        recording["metadata"] = dict(metadata)
        store.finish(metadata["game_id"], recording, metadata)
    except Exception:
        logging.exception("Match %s failed", metadata["game_id"])
        metadata.update(status="failed", finished_at=now(), reason="Simulation failed. See the local server log.")
        if sim is not None and hasattr(sim, "frames"):
            recording = sim.export_recording(dict(metadata), error=metadata["reason"])
            metadata["replay_available"] = True
            recording["metadata"] = dict(metadata)
            store.finish(metadata["game_id"], recording, metadata)
        else:
            store.save_metadata(metadata)
    finally:
        for runner in runners:
            runner.stop()
        if metadata.get("room_id"):
            room_service.room_repository.update_room_status(metadata["room_id"], "finished")


def launch(seed, participants, packages, room_id=None):
    game_id = f"game-{uuid.uuid4().hex}"
    metadata = {"game_id": game_id, "seed": seed, "room_id": room_id,
                "players": [p["name"] for p in participants], "participants": participants,
                "status": "queued", "created_at": now(), "winner": None, "replay_available": False}
    store.save_metadata(metadata)
    workers.submit(_run_match, dict(metadata), packages)
    return {"game_id": game_id, "room_id": room_id}


@app.post("/game/create")
def create_game(seed: int = 42):
    if not 0 <= seed <= 2**31 - 1:
        raise ValueError("Seed must be between 0 and 2147483647")
    participants = [{"player_id": p.value, "name": f"Demo {i + 1}", "bot_id": "demo-v1",
                     "bot_name": "Demo bot", "bot_version": "v1"}
                    for i, p in enumerate(PlayerId.all_players())]
    return launch(seed, participants, [None] * 4)


@app.get("/games")
def list_games():
    return {"games": store.list_games()}


@app.get("/games/{game_id}")
def get_game_metadata(game_id: str):
    return store.metadata(game_id)


@app.get("/game/{game_id}/replay")
def replay(game_id: str):
    recording = store.replay(game_id)
    if recording is None:
        raise HTTPException(409, "This run has no saved replay yet. Check its status on Matches.")
    return recording


@app.get("/game/{game_id}/state")
def state(game_id: str, player: str | None = None):
    if player is not None:
        raise HTTPException(403, "Private player views are not available in this local viewer.")
    return replay(game_id)["frames"][-1]["state"]


@app.get("/rooms")
def list_rooms():
    return {"rooms": room_service.list_rooms()}


@app.get("/rooms/{room_id}")
def get_room(room_id: str):
    room = room_service.get_room(room_id).to_dict()
    matches = [g for g in store.list_games() if g.get("room_id") == room_id]
    room["game"] = matches[0] if matches else None
    return {"room": room}


@app.post("/rooms")
def create_room(room_name: str = "New room", created_by: str = "Player"):
    if not room_name.strip() or not created_by.strip() or max(len(room_name), len(created_by)) > 80:
        raise ValueError("Room and player names must contain 1–80 characters")
    with mutation_lock:
        return {"room": room_service.create_room(room_name.strip(), created_by.strip()).to_dict()}


@app.post("/rooms/{room_id}/join")
def join_room(room_id: str, request: RoomJoinRequest):
    if not request.player_name.strip():
        raise ValueError("Enter a player name")
    with mutation_lock:
        return {"room": room_service.join_room(room_id, request.player_name.strip()).to_dict()}


@app.post("/rooms/{room_id}/ready")
def set_room_ready(room_id: str, request: RoomReadyRequest):
    with mutation_lock:
        room = room_service.get_room(room_id)
        seat = next((s for s in room.seats if s.player_name == request.player_name), None)
        if seat is None:
            raise ValueError("Join this room first")
        if request.ready:
            require_bot(seat.to_dict()["bot_runner"])
        return {"room": room_service.set_ready(room_id, request.player_name, request.ready).to_dict()}


@app.post("/rooms/{room_id}/attach-bot")
def attach_bot(room_id: str, request: AttachBotRequest):
    with mutation_lock:
        package = require_bot(f"{request.bot_name}-{request.bot_version}")
        reference = BotRunner(bot_id=package.bot_id, name=package.name, version=package.version)
        return {"room": room_service.attach_bot(room_id, request.player_name, reference).to_dict()}


@app.post("/rooms/{room_id}/start-game")
def start_room_game(room_id: str, request: StartGameRequest):
    with mutation_lock:
        room = room_service.get_room(room_id)
        if not room.is_ready():
            raise ValueError("All four seats need a valid bot and must be ready")
        packages = [require_bot(s.to_dict()["bot_runner"]) for s in room.seats]
        participants = [{"player_id": pid.value, "name": s.player_name, "bot_id": b.bot_id,
                         "bot_name": b.name, "bot_version": b.version}
                        for pid, s, b in zip(PlayerId.all_players(), room.seats, packages)]
        room_service.start_game(room_id)
        return launch(request.seed, participants, packages, room_id)


@app.get("/bots")
def list_bots():
    return {"bots": bot_registry.list_bots()}


@app.post("/bots/upload")
def upload_bot(request: BotUploadRequest):
    with mutation_lock:
        if bot_registry.get_bot(f"{request.bot_name.strip()}-{request.bot_version.strip()}"):
            raise HTTPException(409, "That version already exists. Choose a new version name.")
        package = bot_registry.register(request.bot_name.strip(), request.bot_version.strip(),
                                       entrypoint=request.entrypoint, description=request.description,
                                       bot_code=request.bot_code if request.use_sandbox else None,
                                       use_sandbox=request.use_sandbox)
        if request.bot_code and request.use_sandbox:
            try:
                compile(request.bot_code, "uploaded-bot.py", "exec")
            except SyntaxError as error:
                package.validated = False
                package.validation_errors = [f"Python syntax error on line {error.lineno}: {error.msg}"]
                bot_registry.bot_repository.update_bot_validation(package.bot_id, False, package.validation_errors)
        return package_data(package)


@app.get("/bots/{bot_id}")
def get_bot(bot_id: str):
    package = bot_registry.get_bot(bot_id)
    if package is None:
        raise KeyError(bot_id)
    return package_data(package)


@app.get("/", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def index():
    return (assets / "index.html").read_text(encoding="utf-8")
