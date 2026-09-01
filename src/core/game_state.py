"""Core domain state types"""
from typing import List, Dict, Optional
from enum import Enum
from ..simulator.types.resource import ResourceType
from ..simulator.types.identifiers import PlayerId


class GamePhase(str, Enum):
    """Game phases"""
    SETUP_FIRST = "SETUP_FIRST"  # First placement round
    SETUP_SECOND = "SETUP_SECOND"  # Second placement round (reverse order)
    NORMAL_PLAY = "NORMAL_PLAY"  # Regular gameplay
    GAME_OVER = "GAME_OVER"  # Game has ended


class GameStatus(str, Enum):
    """Game status"""
    ACTIVE = "ACTIVE"  # Game in progress
    COMPLETED = "COMPLETED"  # Game won
    ERROR = "ERROR"  # Unrecoverable error


class GameState:
    """Complete authoritative game state"""
    def __init__(self):
        self.game_id: str = ""
        self.seed: int = 0
        self.phase: GamePhase = GamePhase.SETUP_FIRST
        self.status: GameStatus = GameStatus.ACTIVE
        
        self.board_state: Optional['BoardState'] = None
        self.bank_state: Optional['BankState'] = None
        self.players: List['PlayerState'] = []
        self.turn_state: Optional['TurnState'] = None
        
        # Game metadata
        self.creation_timestamp: float = 0.0
        self.winner: Optional[PlayerId] = None

    def get_player(self, player_id: PlayerId) -> Optional['PlayerState']:
        """Get a player's state"""
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

    def get_player_order(self) -> List[PlayerId]:
        """Get players in current order"""
        return [p.player_id for p in self.players]

    def is_setup_phase(self) -> bool:
        """Check if in setup phase"""
        return self.phase in (GamePhase.SETUP_FIRST, GamePhase.SETUP_SECOND)

    def is_normal_play_phase(self) -> bool:
        """Check if in normal play phase"""
        return self.phase == GamePhase.NORMAL_PLAY

    def is_game_over(self) -> bool:
        """Check if game has ended"""
        return self.status == GameStatus.COMPLETED

    def __repr__(self):
        return (f"GameState(game_id={self.game_id}, "
                f"phase={self.phase.value}, "
                f"status={self.status.value}, "
                f"players={len(self.players)})")
