"""Database persistence layer for bots, games, and users.

This module provides SQLAlchemy models and database operations to replace
the in-memory services with persistent storage.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    bots = relationship("Bot", back_populates="owner")
    rooms = relationship("Room", back_populates="creator")


class Bot(Base):
    """Bot model for storing bot versions and metadata."""
    __tablename__ = "bots"
    
    id = Column(String, primary_key=True)  # bot_id format: "name-version"
    name = Column(String, nullable=False, index=True)
    version = Column(String, nullable=False)
    entrypoint = Column(String, default="main.py")
    description = Column(Text, default="")
    bot_code = Column(Text, nullable=True)  # Optional bot code for sandboxed execution
    use_sandbox = Column(Boolean, default=False)
    sandbox_config = Column(Text, nullable=True)  # JSON-serialized sandbox config
    
    # Validation status
    validated = Column(Boolean, default=False)
    validation_errors = Column(Text, nullable=True)  # JSON-serialized error list
    
    # Metadata
    owner_id = Column(String, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    owner = relationship("User", back_populates="bots")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert bot to dictionary for API responses."""
        return {
            "bot_id": self.id,
            "name": self.name,
            "version": self.version,
            "entrypoint": self.entrypoint,
            "description": self.description,
            "validated": self.validated,
            "validation_errors": json.loads(self.validation_errors) if self.validation_errors else [],
            "use_sandbox": self.use_sandbox,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Game(Base):
    """Game model for storing game metadata and results."""
    __tablename__ = "games"
    
    id = Column(String, primary_key=True)  # game_id
    room_id = Column(String, ForeignKey("rooms.id"), nullable=True)
    seed = Column(Integer, nullable=False)
    status = Column(String, default="created")  # created, running, completed, failed
    players = Column(Text, nullable=False)  # JSON-serialized list of player IDs
    winner = Column(String, nullable=True)
    turn_count = Column(Integer, default=0)
    
    # Game metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    room = relationship("Room", back_populates="games")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert game to dictionary for API responses."""
        return {
            "game_id": self.id,
            "room_id": self.room_id,
            "seed": self.seed,
            "status": self.status,
            "players": json.loads(self.players) if self.players else [],
            "winner": self.winner,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class Room(Base):
    """Room model for lobby and game coordination."""
    __tablename__ = "rooms"
    
    id = Column(String, primary_key=True)  # room_id
    name = Column(String, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="waiting")  # waiting, playing, completed
    
    # Room configuration
    max_players = Column(Integer, default=4)
    seed = Column(Integer, nullable=True)
    
    # Seats configuration (JSON-serialized)
    seats = Column(Text, nullable=False)  # List of seat configurations
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", back_populates="rooms")
    games = relationship("Game", back_populates="room")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert room to dictionary for API responses."""
        return {
            "room_id": self.id,
            "name": self.name,
            "created_by": self.created_by,
            "status": self.status,
            "max_players": self.max_players,
            "seed": self.seed,
            "seats": json.loads(self.seats) if self.seats else [],
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class DatabaseManager:
    """Manager for database operations."""
    
    def __init__(self, database_url: str = "sqlite:///catan_platform.db"):
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._session: Optional[Session] = None
    
    def create_tables(self) -> None:
        """Create all database tables."""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self) -> Session:
        """Get a database session."""
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session
    
    def close_session(self) -> None:
        """Close the current database session."""
        if self._session is not None:
            self._session.close()
            self._session = None
    
    def __enter__(self):
        """Context manager entry."""
        self._session = self.SessionLocal()
        return self._session
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._session is not None:
            if exc_type is not None:
                self._session.rollback()
            else:
                self._session.commit()
            self._session.close()
            self._session = None


class BotRepository:
    """Repository for bot-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_bot(
        self,
        bot_id: str,
        name: str,
        version: str,
        entrypoint: str = "main.py",
        description: str = "",
        bot_code: Optional[str] = None,
        use_sandbox: bool = False,
        sandbox_config: Optional[Dict[str, Any]] = None,
        owner_id: Optional[str] = None
    ) -> Bot:
        """Create a new bot record."""
        with self.db as session:
            bot = Bot(
                id=bot_id,
                name=name,
                version=version,
                entrypoint=entrypoint,
                description=description,
                bot_code=bot_code,
                use_sandbox=use_sandbox,
                sandbox_config=json.dumps(sandbox_config) if sandbox_config else None,
                owner_id=owner_id
            )
            session.add(bot)
            session.commit()
            session.refresh(bot)
            # Make a copy of attributes before session closes
            return Bot(
                id=bot.id,
                name=bot.name,
                version=bot.version,
                entrypoint=bot.entrypoint,
                description=bot.description,
                bot_code=bot.bot_code,
                use_sandbox=bot.use_sandbox,
                sandbox_config=bot.sandbox_config,
                validated=bot.validated,
                validation_errors=bot.validation_errors,
                owner_id=bot.owner_id,
                created_at=bot.created_at,
                updated_at=bot.updated_at,
            )
    
    def get_bot(self, bot_id: str) -> Optional[Bot]:
        """Get a bot by ID."""
        with self.db as session:
            return session.query(Bot).filter(Bot.id == bot_id).first()
    
    def list_bots(self, owner_id: Optional[str] = None) -> List[Bot]:
        """List all bots, optionally filtered by owner."""
        with self.db as session:
            query = session.query(Bot)
            if owner_id:
                query = query.filter(Bot.owner_id == owner_id)
            return query.order_by(Bot.name, Bot.version).all()
    
    def update_bot_validation(
        self,
        bot_id: str,
        validated: bool,
        validation_errors: Optional[List[str]] = None
    ) -> Optional[Bot]:
        """Update bot validation status."""
        with self.db as session:
            bot = session.query(Bot).filter(Bot.id == bot_id).first()
            if bot:
                bot.validated = validated
                bot.validation_errors = json.dumps(validation_errors) if validation_errors else None
                bot.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(bot)
                # Return a copy to avoid detached instance issues
                return Bot(
                    id=bot.id,
                    name=bot.name,
                    version=bot.version,
                    entrypoint=bot.entrypoint,
                    description=bot.description,
                    bot_code=bot.bot_code,
                    use_sandbox=bot.use_sandbox,
                    sandbox_config=bot.sandbox_config,
                    validated=bot.validated,
                    validation_errors=bot.validation_errors,
                    owner_id=bot.owner_id,
                    created_at=bot.created_at,
                    updated_at=bot.updated_at,
                )
            return None
    
    def delete_bot(self, bot_id: str) -> bool:
        """Delete a bot by ID."""
        with self.db as session:
            bot = session.query(Bot).filter(Bot.id == bot_id).first()
            if bot:
                session.delete(bot)
                session.commit()
                return True
            return False


class GameRepository:
    """Repository for game-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_game(
        self,
        game_id: str,
        seed: int,
        players: List[str],
        room_id: Optional[str] = None
    ) -> Game:
        """Create a new game record."""
        with self.db as session:
            game = Game(
                id=game_id,
                seed=seed,
                players=json.dumps(players),
                room_id=room_id,
                status="created"
            )
            session.add(game)
            session.commit()
            session.refresh(game)
            # Make a copy of attributes before session closes
            return Game(
                id=game.id,
                seed=game.seed,
                players=game.players,
                room_id=game.room_id,
                status=game.status,
                winner=game.winner,
                turn_count=game.turn_count,
                created_at=game.created_at,
                started_at=game.started_at,
                completed_at=game.completed_at,
            )
    
    def get_game(self, game_id: str) -> Optional[Game]:
        """Get a game by ID."""
        with self.db as session:
            return session.query(Game).filter(Game.id == game_id).first()
    
    def list_games(self, room_id: Optional[str] = None) -> List[Game]:
        """List all games, optionally filtered by room."""
        with self.db as session:
            query = session.query(Game)
            if room_id:
                query = query.filter(Game.room_id == room_id)
            return query.order_by(Game.created_at.desc()).all()
    
    def update_game_status(
        self,
        game_id: str,
        status: str,
        winner: Optional[str] = None,
        turn_count: Optional[int] = None
    ) -> Optional[Game]:
        """Update game status and metadata."""
        with self.db as session:
            game = session.query(Game).filter(Game.id == game_id).first()
            if game:
                game.status = status
                if winner is not None:
                    game.winner = winner
                if turn_count is not None:
                    game.turn_count = turn_count
                
                if status == "running" and not game.started_at:
                    game.started_at = datetime.utcnow()
                elif status == "completed" and not game.completed_at:
                    game.completed_at = datetime.utcnow()
                
                session.commit()
                session.refresh(game)
                return game
            return None


class RoomRepository:
    """Repository for room-related database operations."""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def create_room(
        self,
        room_id: str,
        name: str,
        created_by: str,
        max_players: int = 4,
        seats: Optional[List[Dict[str, Any]]] = None
    ) -> Room:
        """Create a new room."""
        if seats is None:
            seats = [{"player_name": None, "ready": False, "bot_runner": None} for _ in range(max_players)]
        
        with self.db as session:
            room = Room(
                id=room_id,
                name=name,
                created_by=created_by,
                max_players=max_players,
                seats=json.dumps(seats),
                status="waiting"
            )
            session.add(room)
            session.commit()
            session.refresh(room)
            return room
    
    def get_room(self, room_id: str) -> Optional[Room]:
        """Get a room by ID."""
        with self.db as session:
            return session.query(Room).filter(Room.id == room_id).first()
    
    def list_rooms(self, created_by: Optional[str] = None) -> List[Room]:
        """List all rooms, optionally filtered by creator."""
        with self.db as session:
            query = session.query(Room)
            if created_by:
                query = query.filter(Room.created_by == created_by)
            return query.order_by(Room.created_at.desc()).all()
    
    def update_room_seats(self, room_id: str, seats: List[Dict[str, Any]]) -> Optional[Room]:
        """Update room seats configuration."""
        with self.db as session:
            room = session.query(Room).filter(Room.id == room_id).first()
            if room:
                room.seats = json.dumps(seats)
                room.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(room)
                return room
            return None
    
    def update_room_status(self, room_id: str, status: str) -> Optional[Room]:
        """Update room status."""
        with self.db as session:
            room = session.query(Room).filter(Room.id == room_id).first()
            if room:
                room.status = status
                room.updated_at = datetime.utcnow()
                session.commit()
                session.refresh(room)
                return room
            return None
    
    def delete_room(self, room_id: str) -> bool:
        """Delete a room by ID."""
        with self.db as session:
            room = session.query(Room).filter(Room.id == room_id).first()
            if room:
                session.delete(room)
                session.commit()
                return True
            return False
