"""Event and replay ordering tests."""

from src.events import EventBus, GameEvent
from src.simulator.types.identifiers import PlayerId


class TestEventBus:
    def test_event_bus_assigns_deterministic_sequence_numbers(self):
        bus = EventBus()
        received = []
        bus.subscribe(lambda event: received.append(event.sequence_number))

        bus.publish(GameEvent("GameStarted", data={"seed": 1}, game_id="G1"))
        bus.publish(GameEvent("TurnStarted", data={"turn": 1}, game_id="G1"))

        assert received == [0, 1]
        assert bus.events[0].sequence_number == 0
        assert bus.events[1].sequence_number == 1

    def test_event_bus_filters_player_only_visibility(self):
        bus = EventBus()
        p1_events = []
        p2_events = []

        bus.subscribe(lambda event: p1_events.append(event.event_type), PlayerId.P1)
        bus.subscribe(lambda event: p2_events.append(event.event_type), PlayerId.P2)

        bus.publish(GameEvent("DiceRolled", game_id="G1", player_id=PlayerId.P1, visibility="PLAYER_ONLY"))
        bus.publish(GameEvent("TradeOfferCreated", game_id="G1", player_id=PlayerId.P2, visibility="PLAYER_ONLY"))

        assert p1_events == ["DiceRolled"]
        assert p2_events == ["TradeOfferCreated"]

    def test_replay_export_contains_ordered_events(self):
        bus = EventBus()
        replay = __import__("src.replay", fromlist=["ReplayRecorder"]).ReplayRecorder()

        bus.publish(GameEvent("GameStarted", game_id="G1", turn_number=0, visibility="PUBLIC"))
        replay.record_event(bus.events[0])

        exported = replay.export()
        assert exported["events"][0]["sequence"] == 0
        assert exported["events"][0]["type"] == "GameStarted"
