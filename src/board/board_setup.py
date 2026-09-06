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
        rng.shuffle(tile_ids)

        if len(tile_ids) != len(resource_slots):
            raise ValueError("Tile and resource slot counts must match.")

        desert_tile_id: Optional[TileId] = None
        assigned_tokens = list(cls.STANDARD_TOKENS)
        rng.shuffle(assigned_tokens)

        for tile_id, resource_type in zip(tile_ids, resource_slots):
            board_state.tiles[tile_id] = TileState(
                tile_id=str(tile_id),
                resource_type=resource_type,
                number_token=None,
                has_robber=False,
            )
            if resource_type is None:
                desert_tile_id = tile_id

        if desert_tile_id is None:
            raise ValueError("Board setup requires exactly one desert tile.")

        land_tile_ids = [tile_id for tile_id in tile_ids if tile_id != desert_tile_id]
        if len(land_tile_ids) != len(cls.STANDARD_TOKENS):
            raise ValueError("Number-token count does not match non-desert tiles.")

        rng.shuffle(land_tile_ids)
        for tile_id, token in zip(land_tile_ids, cls.STANDARD_TOKENS):
            board_state.tiles[tile_id].number_token = token

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
