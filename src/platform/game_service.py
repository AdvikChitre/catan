"""Game metadata service for the platform with database persistence."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .database import DatabaseManager, GameRepository


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
    """Tracks game metadata and room associations for the platform with database persistence."""

    def __init__(self, use_database: bool = True, database_url: str = "sqlite:///catan_platform.db"):
        self.use_database = use_database
        if use_database:
            self.db_manager = DatabaseManager(database_url)
            self.db_manager.create_tables()
            self.game_repository = GameRepository(self.db_manager)
        else:
            # Fallback to in-memory storage
            self.games: Dict[str, GameRecord] = {}

    def create_game(self, game_id: str, *, room_id: Optional[str] = None, seed: int = 42, players: Optional[List[str]] = None) -> GameRecord:
        if self.use_database:
            db_game = self.game_repository.create_game(
                game_id=game_id,
                seed=seed,
                players=list(players or []),
                room_id=room_id
            )
            players_data = json.loads(db_game.players) if db_game.players else []
            return GameRecord(
                game_id=db_game.id,
                room_id=db_game.room_id,
                seed=db_game.seed,
                status=db_game.status,
                created_at=db_game.created_at.isoformat() if db_game.created_at else datetime.now(timezone.utc).isoformat(),
                winner=db_game.winner,
                players=players_data,
                metadata={"source": "simulator"},
            )
        else:
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
        if self.use_database:
            db_game = self.game_repository.get_game(game_id)
            if db_game:
                players_data = json.loads(db_game.players) if db_game.players else []
                return GameRecord(
                    game_id=db_game.id,
                    room_id=db_game.room_id,
                    seed=db_game.seed,
                    status=db_game.status,
                    created_at=db_game.created_at.isoformat() if db_game.created_at else datetime.now(timezone.utc).isoformat(),
                    winner=db_game.winner,
                    players=players_data,
                    metadata={"source": "simulator"},
                )
            return None
        else:
            return self.games.get(game_id)

    def list_games(self, room_id: Optional[str] = None) -> List[GameRecord]:
        if self.use_database:
            db_games = self.game_repository.list_games(room_id=room_id)
            return [
                GameRecord(
                    game_id=game.id,
                    room_id=game.room_id,
                    seed=game.seed,
                    status=game.status,
                    created_at=game.created_at.isoformat() if game.created_at else datetime.now(timezone.utc).isoformat(),
                    winner=game.winner,
                    players=json.loads(game.players) if game.players else [],
                    metadata={"source": "simulator"},
                )
                for game in db_games
            ]
        else:
            return list(self.games.values())

    def update_status(self, game_id: str, *, status: str, winner: Optional[str] = None, players: Optional[List[str]] = None) -> Optional[GameRecord]:
        if self.use_database:
            db_game = self.game_repository.update_game_status(
                game_id=game_id,
                status=status,
                winner=winner,
                turn_count=None
            )
            if db_game:
                players_data = json.loads(db_game.players) if db_game.players else []
                return GameRecord(
                    game_id=db_game.id,
                    room_id=db_game.room_id,
                    seed=db_game.seed,
                    status=db_game.status,
                    created_at=db_game.created_at.isoformat() if db_game.created_at else datetime.now(timezone.utc).isoformat(),
                    winner=db_game.winner,
                    players=players_data,
                    metadata={"source": "simulator"},
                )
            return None
        else:
            record = self.games.get(game_id)
            if record is None:
                return None
            record.status = status
            if winner is not None:
                record.winner = winner
            if players is not None:
                record.players = list(players)
            return record
