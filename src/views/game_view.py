"""Game view - player-specific filtered state"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..core import GameState
from ..simulator.types.identifiers import PlayerId
from ..simulator.types.resource import DevelopmentCardType, ResourceType


@dataclass(frozen=True)
class TileView:
    """Public tile information visible to all players."""
    tile_id: str
    resource_type: Optional[ResourceType]
    number_token: Optional[int]
    has_robber: bool


@dataclass(frozen=True)
class PlayerView:
    """Public player summary, with hidden information omitted."""
    player_id: PlayerId
    resources: Dict[ResourceType, int] = field(default_factory=dict)
    development_cards: Dict[DevelopmentCardType, int] = field(default_factory=dict)
    roads_remaining: int = 0
    settlements_remaining: int = 0
    cities_remaining: int = 0
    knights_played: int = 0
    victory_points: int = 0
    has_longest_road: bool = False
    has_largest_army: bool = False


@dataclass(frozen=True)
class BoardView:
    """Public board data used by bots."""
    tiles: List[TileView] = field(default_factory=list)
    robber_tile_id: Optional[str] = None


@dataclass(frozen=True)
class TurnView:
    """Public turn snapshot."""
    turn_number: int = 0
    current_player: Optional[PlayerId] = None
    phase: str = ""


@dataclass(frozen=True)
class GameView:
    """Player-specific immutable view of the game state."""
    game_id: str
    self: PlayerView
    opponents: List[PlayerView]
    board: BoardView
    turn: TurnView
    game_state: Any = field(default=None, repr=False)

    @property
    def player_id(self) -> PlayerId:
        return self.self.player_id
