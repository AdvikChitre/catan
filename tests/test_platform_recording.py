"""Replay contract, privacy, persistence and room integration regressions."""
import copy
import json
import threading
import time
import uuid

from fastapi.testclient import TestClient

from src.events import GameEvent
from src.platform.recording import RecordingSimulator, public_state
from src.platform.replay_store import ReplayStore
from src.simulator.run import DummyBot
from src.simulator.types.identifiers import PlayerId
from src.simulator.types.resource import DevelopmentCardType, ResourceType


def simulator():
    sim = RecordingSimulator(seed=41)
    sim.register_bots({pid: DummyBot() for pid in PlayerId.all_players()})
    sim.begin_recording()
    return sim


def test_recording_captures_real_setup_and_every_roll_without_aliases():
    sim = simulator()
    initial = copy.deepcopy(sim.frames[0])
    sim.run()
    replay = sim.export_recording({"game_id": "game-test"})
    assert sim.frames[0] == initial
    assert not sim.frames[0]["state"]["buildings"]
    assert len(sim.frames[-1]["state"]["buildings"]) >= 8
    assert len(sim.frames[-1]["state"]["roads"]) >= 8
    assert len([f for f in sim.frames if any(e["type"] == "DiceRolled" for e in f["events"])]) >= 8
    assert replay["result"]["status"] == "completed"
    assert replay["result"]["winner"] is not None
    assert replay["result"]["statistics"]["roll_count"] >= 8
    assert replay["geometry"]["valid_hex_topology"] is True
    assert [f["sequence"] for f in sim.frames] == list(range(len(sim.frames)))
    assert sim.frames[-1]["state"] == public_state(sim)
    json.dumps(replay)


def test_private_events_unknown_payloads_and_hidden_vp_are_not_exported():
    sim = simulator()
    player = sim.game_state.players[0]
    player.resources[ResourceType.ORE] = 7
    player.development_cards[DevelopmentCardType.VICTORY_POINT] = 3
    sim.event_bus.publish(GameEvent("Secret", data={"secret": "never-export"}, visibility="PRIVATE", player_id=PlayerId.P1))
    sim.event_bus.publish(GameEvent("DevelopmentCardPurchased", data={"player_id": "P1", "card": "VICTORY_POINT"}, visibility="PUBLIC"))
    sim.event_bus.publish(GameEvent("FutureEvent", data={"secret": "never-export"}, visibility="PUBLIC"))
    replay = sim.export_recording({})
    exported = json.dumps(replay)
    assert "never-export" not in exported
    assert "VICTORY_POINT" not in exported
    assert all("resources" not in p for f in replay["frames"] for p in f["state"]["players"])
    assert replay["frames"][-1]["state"]["players"][0]["victory_points"] == 0


def test_recording_survives_a_new_store_and_recovers_interrupted_jobs(tmp_path):
    store = ReplayStore(tmp_path)
    sim = simulator()
    sim.run()
    metadata = {"game_id": "game-test", "status": "running", "created_at": "2026-01-01"}
    replay = sim.export_recording(metadata)
    store.finish("game-test", replay, metadata)
    store.save_metadata({"game_id": "game-interrupted", "status": "queued", "created_at": "2026-01-02"})
    fresh = ReplayStore(tmp_path)
    fresh.recover()
    assert fresh.replay("game-test") == replay
    assert fresh.metadata("game-test")["replay_available"]
    assert fresh.metadata("game-interrupted")["status"] == "failed"
    assert not list(tmp_path.glob("*.tmp"))


def test_room_roundtrip_preserves_versions_and_selection_clears_ready():
    from src.platform.server import app
    client = TestClient(app)
    suffix = uuid.uuid4().hex[:8]
    room = client.post('/rooms', params={"room_name": "Regression", "created_by": "A"}).json()["room"]
    rid = room["room_id"]
    assert client.post(f'/rooms/{rid}/ready', json={"player_name": "A"}).status_code == 400
    assert client.post(f'/rooms/{rid}/join', json={"player_name": "A"}).status_code == 400
    assert client.post(f'/rooms/{rid}/attach-bot', json={"player_name": "A", "bot_name": "missing"}).status_code == 400
    for who in ["A", "B", "C", "D"]:
        if who != "A":
            assert client.post(f'/rooms/{rid}/join', json={"player_name": who}).status_code == 200
        bot_name = f"{who}-{suffix}"
        payload = {"bot_name": bot_name, "bot_version": "v1"}
        assert client.post('/bots/upload', json=payload).status_code == 200
        assert client.post('/bots/upload', json=payload).status_code == 409
        assert client.post(f'/rooms/{rid}/attach-bot', json={"player_name": who, **payload}).status_code == 200
        assert client.post(f'/rooms/{rid}/ready', json={"player_name": who}).status_code == 200
    loaded = client.get(f'/rooms/{rid}').json()["room"]
    assert all(s["bot_runner"] and s["ready"] for s in loaded["seats"])
    assert client.post(f'/rooms/{rid}/attach-bot', json={"player_name": "A", "bot_name": f"A-{suffix}"}).status_code == 200
    loaded = client.get(f'/rooms/{rid}').json()["room"]
    assert not loaded["seats"][0]["ready"]
    assert all(s["ready"] and s["bot_runner"] for s in loaded["seats"][1:])
    assert client.post(f'/rooms/{rid}/start-game', json={"seed": 1}).status_code == 400
    assert client.get('/game/game-missing/state?player=P1').status_code == 403


def test_worker_does_not_block_api_and_replay_is_available_only_when_saved(monkeypatch):
    from src.platform import server
    entered = threading.Event()
    release = threading.Event()
    original = server._run_match

    def blocked_run(metadata, packages):
        entered.set()
        assert release.wait(5)
        return original(metadata, packages)

    monkeypatch.setattr(server, "_run_match", blocked_run)
    client = TestClient(server.app)
    gid = client.post('/game/create').json()["game_id"]
    try:
        assert entered.wait(5)
        assert client.get('/games').status_code == 200
        assert client.get(f'/game/{gid}/replay').status_code == 409
    finally:
        release.set()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        if client.get(f'/games/{gid}').json()["replay_available"]:
            break
        time.sleep(.02)
    assert client.get(f'/game/{gid}/replay').status_code == 200
