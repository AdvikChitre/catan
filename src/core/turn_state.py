"""Turn state"""
from typing import Optional
from ..simulator.types.identifiers import PlayerId


class TurnState:
    """Current turn information"""
    def __init__(self):
        self.current_player: Optional[PlayerId] = None
        self.turn_number: int = 0
        self.dice_roll: Optional[int] = None
        self.phase: str = "PRE_ROLL"  # PRE_ROLL, ROLLED, PLAYING, END_TURN

    def is_pre_roll(self) -> bool:
        """Check if in pre-roll phase"""
        return self.phase == "PRE_ROLL"

    def is_rolled(self) -> bool:
        """Check if dice have been rolled"""
        return self.phase == "ROLLED"

    def is_playing(self) -> bool:
        """Check if in main playing phase"""
        return self.phase == "PLAYING"

    def __repr__(self):
        return (f"TurnState(player={self.current_player.value if self.current_player else 'None'}, "
                f"turn={self.turn_number}, roll={self.dice_roll}, phase={self.phase})")
