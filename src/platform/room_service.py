"""In-memory room and lobby service for the platform."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .bot_runner import BotRunner


@dataclass
class RoomSeat:
    player_name: Optional[str] = None
    bot_runner: Optional[BotRunner] = None
    ready: bool = False


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


class RoomService:
    """Minimal in-memory lobby service used for the MVP platform prototype."""

    def __init__(self):
        self.rooms: Dict[str, Room] = {}

    def create_room(self, room_name: str, created_by: str) -> Room:
        room_id = f"room-{len(self.rooms) + 1}"
        room = Room(room_id=room_id, name=room_name, created_by=created_by)
        room.join(created_by)
        self.rooms[room_id] = room
        return room

    def get_room(self, room_id: str) -> Room:
        try:
            return self.rooms[room_id]
        except KeyError as exc:
            raise KeyError(f"Room '{room_id}' not found") from exc

    def list_rooms(self) -> List[Dict[str, object]]:
        return [
            {
                "room_id": room.room_id,
                "name": room.name,
                "created_by": room.created_by,
                "status": room.status,
                "seats": [
                    {
                        "player_name": seat.player_name,
                        "ready": seat.ready,
                        "bot_runner": seat.bot_runner.bot_id if seat.bot_runner else None,
                    }
                    for seat in room.seats
                ],
            }
            for room in self.rooms.values()
        ]

    def join_room(self, room_id: str, player_name: str) -> Room:
        room = self.get_room(room_id)
        seat = room.join(player_name)
        if seat.player_name == player_name:
            return room
        raise ValueError("Unable to join room")

    def set_ready(self, room_id: str, player_name: str, ready: bool) -> Room:
        room = self.get_room(room_id)
        room.set_ready(player_name, ready)
        return room

    def attach_bot(self, room_id: str, player_name: str, bot_runner: BotRunner) -> Room:
        room = self.get_room(room_id)
        for idx, seat in enumerate(room.seats):
            if seat.player_name == player_name:
                seat.bot_runner = bot_runner
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
        return room
