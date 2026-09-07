"""Tests for the platform adapter."""

from fastapi.testclient import TestClient

from src.platform.server import app


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
