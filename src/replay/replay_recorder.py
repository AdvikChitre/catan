"""Replay recorder"""
from typing import List, Optional
from ..events import GameEvent


class ReplayRecorder:
    """Records game metadata, seed, initial board, events, and final result"""
    def __init__(self):
        self.events: List[GameEvent] = []
        self.metadata: dict = {}

    def record_event(self, event: GameEvent) -> None:
        """Record a game event"""
        self.events.append(event)

    def export(self) -> dict:
        """Export replay data for web client"""
        return {
            "metadata": self.metadata,
            "events": self.events,
        }
