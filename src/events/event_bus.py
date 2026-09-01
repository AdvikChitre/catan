"""Event bus"""
from typing import Callable, List
from .game_event import GameEvent


class EventBus:
    """Delivers game events to bots and replay recorder"""
    def __init__(self):
        self.events: List[GameEvent] = []
        self.sequence_counter: int = 0
        self.subscribers: List[Callable[[GameEvent], None]] = []

    def subscribe(self, callback: Callable[[GameEvent], None]) -> None:
        """Subscribe to game events"""
        self.subscribers.append(callback)

    def publish(self, event: GameEvent) -> None:
        """Publish a game event"""
        event.sequence_number = self.sequence_counter
        self.sequence_counter += 1
        self.events.append(event)
        for subscriber in self.subscribers:
            subscriber(event)
