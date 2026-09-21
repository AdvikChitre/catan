"""Minimal JSON contracts for platform-to-browser communication.

This file documents the canonical serialized shapes used by the live simulator UI.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PublicPlayerSummary:
    player_id: str
    victory_points: int = 0


@dataclass
class PublicGameState:
    game_id: str
    phase: str = "INIT"
    turn_number: int = 0
    current_player: Optional[str] = None
    players: List[PublicPlayerSummary] = field(default_factory=list)
    winner: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "phase": self.phase,
            "turn_number": self.turn_number,
            "current_player": self.current_player,
            "players": [
                {"player_id": p.player_id, "victory_points": p.victory_points}
                for p in self.players
            ],
            "winner": self.winner,
        }


@dataclass
class GameEventMessage:
    sequence: int
    type: str
    game_id: str
    turn_number: int
    player_id: Optional[str] = None
    visibility: str = "PUBLIC"
    data: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sequence": self.sequence,
            "type": self.type,
            "game_id": self.game_id,
            "turn_number": self.turn_number,
            "player_id": self.player_id,
            "visibility": self.visibility,
            "data": self.data or {},
        }
