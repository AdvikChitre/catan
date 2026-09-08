"""Room and lobby service for the platform with database persistence."""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .bot_runner import BotRunner
from .database import DatabaseManager, RoomRepository


@dataclass
class RoomSeat:
    player_name: Optional[str] = None
    bot_runner: Optional[BotRunner] = None
    ready: bool = False

    def to_dict(self) -> Dict[str, object]:
        return {
            "player_name": self.player_name,
            "ready": self.ready,
            "bot_runner": self.bot_runner.bot_id if self.bot_runner and hasattr(self.bot_runner, 'bot_id') else None,
        }


@dataclass
class Room:
    room_id: str
    name: str
    seats: List[RoomSeat] = field(default_factory=lambda: [RoomSeat() for _ in range(4)])
    created_by: Optional[str] = None
    status: str = "waiting"

    def join(self, player_name: str) -> RoomSeat:
        for seat in self.seats:
            if seat.player_name is None:
                seat.player_name = player_name
                seat.ready = False
                return seat
        raise ValueError("Room is full")

    def set_bot(self, seat_index: int, bot_runner: BotRunner) -> None:
        if seat_index < 0 or seat_index >= len(self.seats):
            raise IndexError("Seat index out of range")
        self.seats[seat_index].bot_runner = bot_runner

    def set_ready(self, player_name: str, ready: bool) -> None:
        for seat in self.seats:
            if seat.player_name == player_name:
                seat.ready = ready
                return
        raise ValueError(f"Player '{player_name}' not found in room")

    def is_ready(self) -> bool:
        return len(self.seats) == 4 and all(seat.player_name is not None and seat.ready for seat in self.seats)

    def to_dict(self) -> Dict[str, object]:
        return {
            "room_id": self.room_id,
            "name": self.name,
            "created_by": self.created_by,
            "status": self.status,
            "seats": [seat.to_dict() for seat in self.seats],
        }


class RoomService:
    """Lobby service for the platform with database persistence."""

    def __init__(self, use_database: bool = True, database_url: str = "sqlite:///catan_platform.db"):
        self.use_database = use_database
        if use_database:
            self.db_manager = DatabaseManager(database_url)
            self.db_manager.create_tables()
            self.room_repository = RoomRepository(self.db_manager)
        else:
            # Fallback to in-memory storage
            self.rooms: Dict[str, Room] = {}
            self._room_counter = 0

    def create_room(self, room_name: str, created_by: str) -> Room:
        if self.use_database:
            room_id = f"room-{uuid.uuid4().hex[:8]}"
            seats = [{"player_name": None, "ready": False, "bot_runner": None} for _ in range(4)]
            seats[0]["player_name"] = created_by  # Creator takes first seat
            
            db_room = self.room_repository.create_room(
                room_id=room_id,
                name=room_name,
                created_by=created_by,
                max_players=4,
                seats=seats
            )
            
            # Convert to Room object
            seats_data = json.loads(db_room.seats) if db_room.seats else []
            room_seats = []
            for seat in seats_data:
                # Convert bot_runner from string (bot_id) to BotRunner if possible
                bot_runner_id = seat.get("bot_runner")
                bot_runner = None
                if bot_runner_id:
                    # For now, keep as string since we don't have access to bot_registry here
                    # The bot will be reconstructed when needed in the game start logic
                    bot_runner = bot_runner_id
                
                room_seats.append(RoomSeat(
                    player_name=seat.get("player_name"),
                    bot_runner=bot_runner,
                    ready=seat.get("ready", False)
                ))
            
            room = Room(
                room_id=db_room.id,
                name=db_room.name,
                created_by=db_room.created_by,
                status=db_room.status,
                seats=room_seats
            )
            return room
        else:
            self._room_counter += 1
            room_id = f"room-{self._room_counter}"
            room = Room(room_id=room_id, name=room_name, created_by=created_by)
            room.join(created_by)
            self.rooms[room_id] = room
            return room

    def get_room(self, room_id: str) -> Room:
        if self.use_database:
            db_room = self.room_repository.get_room(room_id)
            if db_room:
                seats_data = json.loads(db_room.seats) if db_room.seats else []
                return Room(
                    room_id=db_room.id,
                    name=db_room.name,
                    created_by=db_room.created_by,
                    status=db_room.status,
                    seats=[RoomSeat(**seat) for seat in seats_data]
                )
            raise KeyError(f"Room '{room_id}' not found")
        else:
            try:
                return self.rooms[room_id]
            except KeyError as exc:
                raise KeyError(f"Room '{room_id}' not found") from exc

    def list_rooms(self, created_by: Optional[str] = None) -> List[Dict[str, object]]:
        if self.use_database:
            db_rooms = self.room_repository.list_rooms(created_by=created_by)
            return [
                {
                    "room_id": room.id,
                    "name": room.name,
                    "created_by": room.created_by,
                    "status": room.status,
                    "seats": json.loads(room.seats) if room.seats else [],
                }
                for room in db_rooms
            ]
        else:
            return [room.to_dict() for room in self.rooms.values()]

    def join_room(self, room_id: str, player_name: str) -> Room:
        room = self.get_room(room_id)
        seat = room.join(player_name)
        
        if self.use_database:
            # Update database
            seats = [seat.to_dict() for seat in room.seats]
            self.room_repository.update_room_seats(room_id, seats)
        
        if seat.player_name == player_name:
            return room
        raise ValueError("Unable to join room")

    def set_ready(self, room_id: str, player_name: str, ready: bool) -> Room:
        room = self.get_room(room_id)
        room.set_ready(player_name, ready)
        
        if self.use_database:
            # Update database
            seats = [seat.to_dict() for seat in room.seats]
            self.room_repository.update_room_seats(room_id, seats)
        
        return room

    def attach_bot(self, room_id: str, player_name: str, bot_runner: BotRunner) -> Room:
        room = self.get_room(room_id)
        for idx, seat in enumerate(room.seats):
            if seat.player_name == player_name:
                seat.bot_runner = bot_runner
                
                if self.use_database:
                    # Store bot_runner.bot_id in database instead of the object
                    seats = []
                    for s in room.seats:
                        seat_dict = {
                            "player_name": s.player_name,
                            "ready": s.ready,
                            "bot_runner": s.bot_runner.bot_id if s.bot_runner and hasattr(s.bot_runner, 'bot_id') else None
                        }
                        seats.append(seat_dict)
                    self.room_repository.update_room_seats(room_id, seats)
                
                return room
        raise ValueError(f"Player '{player_name}' not found in room")

    def can_start_game(self, room_id: str) -> bool:
        room = self.get_room(room_id)
        return room.is_ready()

    def start_game(self, room_id: str) -> Room:
        room = self.get_room(room_id)
        if not room.is_ready():
            raise ValueError("Room is not ready to start")
        room.status = "playing"
        
        if self.use_database:
            self.room_repository.update_room_status(room_id, "playing")
        
        return room
