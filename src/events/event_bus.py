"""Event bus"""
from __future__ import annotations

from typing import Callable, Dict, List, Optional, Tuple

from ..simulator.types.identifiers import PlayerId
from .game_event import GameEvent


class EventBus:
    """Delivers game events to bots and replay recorder with deterministic ordering."""
    def __init__(self):
        self.events: List[GameEvent] = []
        self.sequence_counter: int = 0
        self.subscribers: List[Tuple[Optional[PlayerId], Callable[[GameEvent], None]]] = []

    def subscribe(self, callback: Callable[[GameEvent], None], player_id: Optional[PlayerId] = None) -> None:
        """Subscribe a callback for all events or a specific player."""
        self.subscribers.append((player_id, callback))

    def publish(self, event: GameEvent) -> None:
        """Publish a game event to all relevant subscribers."""
        event.sequence_number = self.sequence_counter
        self.sequence_counter += 1
        self.events.append(event)

        for player_id, subscriber in self.subscribers:
            if player_id is None or event.is_visible_to(player_id):
                subscriber(event)

    def clear(self) -> None:
        """Reset the event bus state."""
        self.events.clear()
        self.sequence_counter = 0
        self.subscribers.clear()
