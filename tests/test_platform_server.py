"""Tests for the platform adapter."""

import os
import tempfile
import time
import uuid
from fastapi.testclient import TestClient

# Use a temporary database for testing
test_db_path = tempfile.mktemp(suffix=".db")
os.environ["CATAN_DB_URL"] = f"sqlite:///{test_db_path}"

from src.platform.server import app

print([(list(r.methods), r.path) for r in app.routes if hasattr(r, 'methods')])

client = TestClient(app)

PLAYER_CODE = """from src.player import Player
class TestPlayer(Player):
    def choose_action(self, view, options): return options[0]
"""


def player_payload(name, version="v1"):
    return {"bot_name": name, "bot_version": version, "entrypoint": "main.py",
            "use_sandbox": True, "bot_code": PLAYER_CODE}


def create_game(seed=42):
    suffix = uuid.uuid4().hex[:8]
    names = [f"A-{suffix}", f"B-{suffix}", f"C-{suffix}", f"D-{suffix}"]
    room_id = client.post("/rooms", params={"room_name": f"Test {suffix}", "created_by": names[0]}).json()["room"]["room_id"]
    for name in names[1:]:
        assert client.post(f"/rooms/{room_id}/join", json={"player_name": name}).status_code == 200
    for name in names:
        bot = f"player-{name}"
        assert client.post("/bots/upload", json=player_payload(bot)).status_code == 200
        assert client.post(f"/rooms/{room_id}/attach-bot", json={"player_name": name, "bot_name": bot}).status_code == 200
        assert client.post(f"/rooms/{room_id}/ready", json={"player_name": name, "ready": True}).status_code == 200
    return client.post(f"/rooms/{room_id}/start-game", json={"seed": seed})


def wait_for_recording(game_id):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        metadata = client.get(f"/games/{game_id}").json()
        if metadata.get("replay_available"):
            return metadata
        assert metadata["status"] != "failed", metadata
        time.sleep(0.02)
    raise AssertionError("Simulation did not finish")

def cleanup_test_db():
    """Clean up test database after tests."""
    if os.path.exists(test_db_path):
        try:
            os.remove(test_db_path)
        except Exception:
            pass

# Run cleanup at module exit
import atexit
atexit.register(cleanup_test_db)


def test_create_game_returns_game_id():
    response = create_game(99)
    assert response.status_code == 200
    body = response.json()
    assert "game_id" in body
    assert body["game_id"].startswith("game-")


def test_state_route_for_created_game():
    create_response = create_game(7)
    game_id = create_response.json()["game_id"]

    wait_for_recording(game_id)
    state_response = client.get(f"/game/{game_id}/state")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["game_id"] == game_id
    assert "players" in state


def test_replay_route_for_created_game():
    create_response = create_game(11)
    game_id = create_response.json()["game_id"]

    wait_for_recording(game_id)
    replay_response = client.get(f"/game/{game_id}/replay")
    assert replay_response.status_code == 200
    replay = replay_response.json()
    assert "metadata" in replay and "events" in replay


def test_room_can_start_game_when_ready():
    create_room = client.post("/rooms", params={"room_name": "Lobby A", "created_by": "Alice"})
    room_id = create_room.json()["room"]["room_id"]

    for player in ["Bob", "Carol", "Dave"]:
        room_join = client.post(f"/rooms/{room_id}/join", json={"player_name": player})
        assert room_join.status_code == 200

    for player in ["Alice", "Bob", "Carol", "Dave"]:
        registered = client.post("/bots/upload", json=player_payload(f"bot-{player.lower()}"))
        assert registered.status_code == 200
        attach = client.post(f"/rooms/{room_id}/attach-bot", json={"player_name": player, "bot_name": f"bot-{player.lower()}"})
        assert attach.status_code == 200
        ready = client.post(f"/rooms/{room_id}/ready", json={"player_name": player, "ready": True})
        assert ready.status_code == 200

    started = client.post(f"/rooms/{room_id}/start-game", json={"seed": 123})
    assert started.status_code == 200
    assert "game_id" in started.json()
    metadata = wait_for_recording(started.json()["game_id"])
    assert [p["bot_id"] for p in metadata["participants"]] == [f"bot-{n}-v1" for n in ["alice", "bob", "carol", "dave"]]
    assert client.post(f"/rooms/{room_id}/start-game", json={"seed": 123}).status_code == 400


def test_list_and_upload_bot_registry():
    list_response = client.get("/bots")
    assert list_response.status_code == 200

    upload_response = client.post(
        "/bots/upload",
        json={**player_payload("alpha"), "description": "first player version"},
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body["validated"] is True
    assert body["bot_id"] == "alpha-v1"

    detail = client.get("/bots/alpha-v1")
    assert detail.status_code == 200
    assert detail.json()["version"] == "v1"

    invalid = client.post(
        "/bots/upload",
        json={**player_payload("", "v2")},
    )
    assert invalid.status_code == 200
    assert invalid.json()["validated"] is False


def test_upload_sandboxed_bot():
    """Test uploading a sandboxed bot with code."""
    bot_code = """
from src.player import Player
class MyPlayer(Player):
    def choose_action(self,view,options): return options[0]
"""
    upload_response = client.post(
        "/bots/upload",
        json={
            "bot_name": "sandboxed-bot",
            "bot_version": "v1",
            "entrypoint": "main.py",
            "description": "A sandboxed bot",
            "use_sandbox": True,
            "bot_code": bot_code,
        }
    )
    assert upload_response.status_code == 200
    body = upload_response.json()
    assert body["validated"] is True
    assert body["bot_id"] == "sandboxed-bot-v1"
    assert body["use_sandbox"] is True


def test_game_metadata_endpoints():
    create_response = create_game(123)
    assert create_response.status_code == 200
    game_id = create_response.json()["game_id"]

    list_response = client.get("/games")
    assert list_response.status_code == 200
    assert any(item["game_id"] == game_id for item in list_response.json()["games"])

    detail_response = client.get(f"/games/{game_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["game_id"] == game_id
    assert detail_response.json()["seed"] == 123
