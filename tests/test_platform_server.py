"""Tests for the platform adapter."""

from fastapi.testclient import TestClient

from src.platform.server import app

print([(list(r.methods), r.path) for r in app.routes if hasattr(r, 'methods')])

client = TestClient(app)


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
        params={
            "bot_name": "alpha",
            "bot_version": "v1",
            "entrypoint": "main.py",
            "description": "first bot version",
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
        params={"bot_name": "", "bot_version": "v2", "entrypoint": "main.py"},
    )
    assert invalid.status_code == 200
    assert invalid.json()["validated"] is False
