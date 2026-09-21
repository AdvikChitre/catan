"""Deterministic board setup utilities for Catan."""

from __future__ import annotations

from typing import Dict, List, Optional

from .board_geometry import BoardGeometry
from ..core.board_state import BoardState
from ..core.building import TileState
from ..simulator.types.identifiers import TileId
from ..simulator.types.resource import ResourceType
from ..simulation.seeded_rng import SeededRng


class BoardSetup:
    """Randomizes land/resources and assigns number tokens deterministically."""

    STANDARD_RESOURCE_COUNTS: Dict[ResourceType, int] = {
        ResourceType.WOOD: 4,
        ResourceType.BRICK: 3,
        ResourceType.SHEEP: 4,
        ResourceType.WHEAT: 4,
        ResourceType.ORE: 3,
    }
    STANDARD_TOKENS: List[int] = [
        2, 3, 3, 4, 4, 5, 5, 6, 6, 8, 8, 9, 9, 10, 10, 11, 11, 12,
    ]

    @classmethod
    def build_board_state(cls, board_geometry: BoardGeometry, rng: SeededRng) -> BoardState:
        """Build a randomized board-state with desert and tokens distributed."""
        board_state = BoardState()
        tile_ids = list(board_geometry.tiles.keys())
        resource_slots = []

        for resource_type, count in cls.STANDARD_RESOURCE_COUNTS.items():
            resource_slots.extend([resource_type] * count)
        resource_slots.append(None)

        rng.shuffle(resource_slots)
        # Counterclockwise outside-in spiral, starting at the eastern corner.
        spiral = ['T20','T21','T22','T23','T24','T25','T26','T27','T28','T29','T30','T31',
                  'T10','T11','T12','T13','T14','T15','T00']
        tokens = iter([5,2,6,3,8,10,9,12,11,4,8,10,9,4,5,6,3,11])
        desert_tile_id = None
        for tile_id,resource_type in zip(spiral,resource_slots):
            board_state.tiles[tile_id] = TileState(tile_id,resource_type,
                next(tokens) if resource_type is not None else None,resource_type is None)
            if resource_type is None: desert_tile_id=tile_id
        board_state.robber_tile_id = desert_tile_id
        board_state.tiles[desert_tile_id].has_robber = True
        return board_state

    @classmethod
    def shuffle_development_deck(cls, rng: SeededRng):
        """Return a shuffled development deck in canonical order."""
        from ..simulator.types.resource import DevelopmentCardType

        deck = []
        deck.extend([DevelopmentCardType.KNIGHT] * 14)
        deck.extend([DevelopmentCardType.VICTORY_POINT] * 5)
        deck.extend([DevelopmentCardType.ROAD_BUILDING] * 2)
        deck.extend([DevelopmentCardType.YEAR_OF_PLENTY] * 2)
        deck.extend([DevelopmentCardType.MONOPOLY] * 2)
        rng.shuffle(deck)
        return deck
