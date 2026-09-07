"""In-memory game metadata service for the platform MVP."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class GameRecord:
    game_id: str
    room_id: Optional[str] = None
    seed: int = 42
    status: str = "created"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    winner: Optional[str] = None
    players: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "game_id": self.game_id,
            "room_id": self.room_id,
            "seed": self.seed,
            "status": self.status,
            "created_at": self.created_at,
            "winner": self.winner,
            "players": self.players,
            "metadata": self.metadata,
        }


class GameService:
    """Tracks game metadata and room associations for the platform."""

    def __init__(self):
        self.games: Dict[str, GameRecord] = {}

    def create_game(self, game_id: str, *, room_id: Optional[str] = None, seed: int = 42, players: Optional[List[str]] = None) -> GameRecord:
        record = GameRecord(
            game_id=game_id,
            room_id=room_id,
            seed=seed,
            players=list(players or []),
            metadata={"source": "simulator"},
        )
        self.games[game_id] = record
        return record

    def get_game(self, game_id: str) -> Optional[GameRecord]:
        return self.games.get(game_id)

    def list_games(self) -> List[GameRecord]:
        return list(self.games.values())

    def update_status(self, game_id: str, *, status: str, winner: Optional[str] = None, players: Optional[List[str]] = None) -> Optional[GameRecord]:
        record = self.games.get(game_id)
        if record is None:
            return None
        record.status = status
        if winner is not None:
            record.winner = winner
        if players is not None:
            record.players = list(players)
        return record
