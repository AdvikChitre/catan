"""Core domain state types"""
from typing import List, Dict, Optional
from .resource import ResourceType
from .identifiers import PlayerId


class GamePhase(str):
    """Game phases"""
    SETUP_FIRST = "SETUP_FIRST"
    SETUP_SECOND = "SETUP_SECOND"
    NORMAL_PLAY = "NORMAL_PLAY"
    GAME_OVER = "GAME_OVER"


class GameStatus(str):
    """Game status"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ERROR = "ERROR"


class GameState:
    """Complete authoritative game state"""
    def __init__(self):
        self.game_id: str = ""
        self.seed: int = 0
        self.phase: str = GamePhase.SETUP_FIRST
        self.status: str = GameStatus.ACTIVE
        self.board_state: Optional['BoardState'] = None
        self.bank_state: Optional['BankState'] = None
        self.players: List['PlayerState'] = []
        self.turn_state: Optional['TurnState'] = None
