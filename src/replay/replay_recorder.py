"""Replay recorder"""
from __future__ import annotations

from typing import Any, Dict, List

from ..events import GameEvent


class ReplayRecorder:
    """Records the ordered event history and metadata for replay playback."""
    def __init__(self):
        self.events: List[GameEvent] = []
        self.metadata: Dict[str, Any] = {}

    def record_event(self, event: GameEvent) -> None:
        """Record a game event."""
        self.events.append(event)

    def export(self) -> Dict[str, Any]:
        """Export replay data for web client or visualizer."""
        return {
            "metadata": dict(self.metadata),
            "events": [
                {
                    "sequence": event.sequence_number,
                    "type": event.event_type,
                    "game_id": event.game_id,
                    "turn_number": event.turn_number,
                    "player_id": event.player_id.value if event.player_id is not None else None,
                    "visibility": event.visibility,
                    "data": event.data,
                }
                for event in self.events
            ],
        }
