"""Action generator"""
from __future__ import annotations

from typing import List

from ..core import GameState
from ..simulator.types.identifiers import PlayerId
from .action_types import AvailableAction


class ActionGenerator:
    """Generates legal available actions for a bot."""
    def __init__(self, game_state: GameState):
        self.game_state = game_state

    def _player(self, player_id: PlayerId):
        return self.game_state.get_player(player_id)

    def _has_resources(self, player, resource_cost):
        for resource_type, amount in resource_cost.items():
            if player.resources.get(resource_type, 0) < amount:
                return False
        return True

    def get_available_actions(
        self, player_id: PlayerId, phase: str
    ) -> List[AvailableAction]:
        """Get available actions for a player in the given phase."""
        player = self._player(player_id)
        if player is None:
            return []

        actions: List[AvailableAction] = []
        if phase == "PRE_ROLL":
            return [AvailableAction("ROLL")]

        if phase == "PLAYING":
            actions.append(AvailableAction("END_TURN"))

            if player.settlements_remaining > 0 and self._has_resources(player, {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WOOD: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.BRICK: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.SHEEP: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WHEAT: 1,
            }):
                actions.append(AvailableAction("BUILD_SETTLEMENT"))

            if player.roads_remaining > 0 and self._has_resources(player, {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WOOD: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.BRICK: 1,
            }):
                actions.append(AvailableAction("BUILD_ROAD"))

            if self._has_resources(player, {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WHEAT: 2,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.ORE: 3,
            }):
                actions.append(AvailableAction("BUILD_CITY"))

            if self._has_resources(player, {
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.WHEAT: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.SHEEP: 1,
                __import__("src.simulator.types.resource", fromlist=["ResourceType"]).ResourceType.ORE: 1,
            }):
                actions.append(AvailableAction("BUY_DEVELOPMENT_CARD"))

        return actions
