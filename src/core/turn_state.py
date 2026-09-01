"""Turn state"""
from typing import Optional
from ..simulator.types.identifiers import PlayerId


class TurnState:
    """Current turn information"""
    def __init__(self):
        self.current_player: Optional[PlayerId] = None
        self.turn_number: int = 0
        self.dice_roll: Optional[int] = None
        self.phase: str = "PRE_ROLL"
