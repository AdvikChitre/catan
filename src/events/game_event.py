"""Game events"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..simulator.types.identifiers import PlayerId


@dataclass
class GameEvent:
    """A single simulator event with deterministic ordering and visibility."""
    event_type: str
    data: Any = None
    game_id: str = ""
    turn_number: int = 0
    player_id: Optional[PlayerId] = None
    visibility: str = "PUBLIC"
    sequence_number: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_visible_to(self, target_player: Optional[PlayerId]) -> bool:
        """Check whether this event is visible to a given player."""
        if self.visibility == "PUBLIC":
            return True
        if self.visibility == "PLAYER_ONLY":
            return target_player == self.player_id
        if self.visibility == "PLAYERS":
            players = self.metadata.get("player_ids", [])
            return target_player in players
        return True

    def __repr__(self):
        return (
            f"GameEvent(type={self.event_type}, sequence={self.sequence_number}, "
            f"player={self.player_id.value if self.player_id else None}, "
            f"visibility={self.visibility})"
        )
