"""Game events"""
from typing import Any, Optional
from ..simulator.types.identifiers import PlayerId


class GameEvent:
    """Base game event"""
    def __init__(self, event_type: str, data: Any = None):
        self.event_type = event_type
        self.sequence_number: int = 0
        self.player_id: Optional[PlayerId] = None
        self.data = data
