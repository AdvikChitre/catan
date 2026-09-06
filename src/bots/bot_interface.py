"""Bot interface"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List

from ..actions import Action, AvailableAction
from ..views import GameView


class BotInterface(ABC):
    """Interface that all bots must implement."""

    @abstractmethod
    def on_game_start(self, view: GameView) -> None:
        """Initialize bot memory when the game begins."""
        pass

    def choose_initial_placement(self, view: GameView, options: List[Any]) -> Any:
        """Return one legal initial placement option."""
        return options[0] if options else None

    @abstractmethod
    def take_turn(self, view: GameView, available_actions: List[AvailableAction]) -> Action:
        """Choose one legal action from the current turn."""
        pass

    def create_trade_offer(self, view: GameView, context: Any) -> Any:
        """Create a trade offer. Simple implementations can reject or return None."""
        return None

    def respond_to_trade(self, view: GameView, offer: Any) -> Any:
        """Answer an incoming trade offer."""
        return {"type": "REJECT"}

    def choose_trade_outcome(self, view: GameView, responses: List[Any]) -> Any:
        """Resolve trade negotiation."""
        return None

    def choose_robber_action(self, view: GameView, options: Any) -> Any:
        """Choose a robber destination or victim."""
        return None

    def choose_road_building(self, view: GameView, options: Any) -> Any:
        """Choose the two-road outcome for a road-building card."""
        return None

    def choose_year_of_plenty(self, view: GameView, options: Any) -> Any:
        """Choose the two resources for a Year of Plenty action."""
        return None

    def choose_monopoly(self, view: GameView, options: Any) -> Any:
        """Choose the monopoly resource type."""
        return None

    def choose_discard(self, view: GameView, options: Any) -> Any:
        """Choose which resources to discard."""
        return None

    @abstractmethod
    def on_event(self, event: dict) -> None:
        """Receive a game event."""
        pass

    def on_game_end(self, result: Any) -> None:
        """Receive final game result."""
        pass
