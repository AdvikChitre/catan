"""Game view builder"""
from __future__ import annotations

from typing import List

from ..core import GameState
from ..core.player_state import PlayerState
from ..simulator.types.identifiers import PlayerId
from .game_view import BoardView, GameView, PlayerView, TileView, TurnView


class GameViewBuilder:
    """Builds player-specific game views with hidden information filtering."""
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def _public_player_view(self, player_state: PlayerState) -> PlayerView:
        return PlayerView(
            player_id=player_state.player_id,
            resources={},
            development_cards={},
            roads_remaining=player_state.roads_remaining,
            settlements_remaining=player_state.settlements_remaining,
            cities_remaining=player_state.cities_remaining,
            knights_played=player_state.largest_army_count,
            victory_points=player_state.get_calculated_victory_points(),
            has_longest_road=player_state.has_longest_road,
            has_largest_army=player_state.has_largest_army,
        )

    def _board_view(self):
        tiles = []
        board_state = self.game_state.board_state
        if board_state is not None:
            for tile_id, tile_state in sorted(board_state.tiles.items(), key=lambda item: str(item[0])):
                tiles.append(
                    TileView(
                        tile_id=str(tile_id),
                        resource_type=tile_state.resource_type,
                        number_token=tile_state.number_token,
                        has_robber=tile_state.has_robber,
                    )
                )
        return BoardView(tiles=tiles, robber_tile_id=str(board_state.robber_tile_id) if board_state and board_state.robber_tile_id is not None else None)

    def build_view(self, player_id: PlayerId) -> GameView:
        """Build a filtered view for the given player."""
        player_state = self.game_state.get_player(player_id)
        if player_state is None:
            raise ValueError(f"Unknown player: {player_id}")

        self_view = PlayerView(
            player_id=player_state.player_id,
            resources=dict(player_state.resources),
            development_cards=dict(player_state.development_cards),
            roads_remaining=player_state.roads_remaining,
            settlements_remaining=player_state.settlements_remaining,
            cities_remaining=player_state.cities_remaining,
            knights_played=player_state.largest_army_count,
            victory_points=player_state.get_calculated_victory_points(),
            has_longest_road=player_state.has_longest_road,
            has_largest_army=player_state.has_largest_army,
        )

        opponent_views: List[PlayerView] = []
        for other in self.game_state.players:
            if other.player_id != player_id:
                opponent_views.append(self._public_player_view(other))

        turn = self.game_state.turn_state
        turn_view = TurnView(
            turn_number=turn.turn_number if turn is not None else 0,
            current_player=turn.current_player if turn is not None else None,
            phase=str(self.game_state.phase.value) if self.game_state.phase is not None else "",
        )

        return GameView(
            game_id=self.game_state.game_id,
            self=self_view,
            opponents=opponent_views,
            board=self._board_view(),
            turn=turn_view,
            game_state=self.game_state,
        )
