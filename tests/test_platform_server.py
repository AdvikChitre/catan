"""Tests for the platform adapter."""

import os
import tempfile
from fastapi.testclient import TestClient

# Use a temporary database for testing
test_db_path = tempfile.mktemp(suffix=".db")
os.environ["CATAN_DB_URL"] = f"sqlite:///{test_db_path}"

from src.platform.server import app

print([(list(r.methods), r.path) for r in app.routes if hasattr(r, 'methods')])

client = TestClient(app)

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
    response = client.post("/game/create", params={"seed": 99})
    assert response.status_code == 200
    body = response.json()
    assert "game_id" in body
    assert body["game_id"].startswith("game-")


def test_state_route_for_created_game():
    create_response = client.post("/game/create", params={"seed": 7})
    game_id = create_response.json()["game_id"]

    state_response = client.get(f"/game/{game_id}/state")
    assert state_response.status_code == 200
    state = state_response.json()
    assert state["game_id"] == game_id
    assert "players" in state


def test_replay_route_for_created_game():
    create_response = client.post("/game/create", params={"seed": 11})
    game_id = create_response.json()["game_id"]

    replay_response = client.get(f"/game/{game_id}/replay")
    assert replay_response.status_code == 200
    replay = replay_response.json()
    assert "metadata" in replay and "events" in replay


def test_room_can_start_game_when_ready():
    create_room = client.post("/rooms", params={"room_name": "Lobby A", "created_by": "Alice"})
    room_id = create_room.json()["room"]["room_id"]

    for player in ["Bob", "Carol", "Dave"]:
        room_join = client.post(f"/rooms/{room_id}/join", params={"player_name": player})
        assert room_join.status_code == 200

    for player in ["Alice", "Bob", "Carol", "Dave"]:
        ready = client.post(f"/rooms/{room_id}/ready", params={"player_name": player, "ready": True})
        assert ready.status_code == 200

    for player in ["Alice", "Bob", "Carol", "Dave"]:
        attach = client.post(f"/rooms/{room_id}/attach-bot", params={"player_name": player, "bot_name": f"bot-{player.lower()}"})
        assert attach.status_code == 200

    started = client.post(f"/rooms/{room_id}/start-game", params={"seed": 123})
    assert started.status_code == 200
    assert "game_id" in started.json()


def test_list_and_upload_bot_registry():
    list_response = client.get("/bots")
    assert list_response.status_code == 200

    upload_response = client.post(
        "/bots/upload",
        json={
            "bot_name": "alpha",
            "bot_version": "v1",
            "entrypoint": "main.py",
            "description": "first bot version",
            "use_sandbox": False,
        },
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
        json={"bot_name": "", "bot_version": "v2", "entrypoint": "main.py", "use_sandbox": False},
    )
    assert invalid.status_code == 200
    assert invalid.json()["validated"] is False


def test_upload_sandboxed_bot():
    """Test uploading a sandboxed bot with code."""
    bot_code = """
def on_game_start(view):
    return {"status": "ready"}

def take_turn(view, available_actions):
    return available_actions[0] if available_actions else None
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
    create_response = client.post("/game/create", params={"seed": 123})
    assert create_response.status_code == 200
    game_id = create_response.json()["game_id"]

    list_response = client.get("/games")
    assert list_response.status_code == 200
    assert any(item["game_id"] == game_id for item in list_response.json()["games"])

    detail_response = client.get(f"/games/{game_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["game_id"] == game_id
    assert detail_response.json()["seed"] == 123
