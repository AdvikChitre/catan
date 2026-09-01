"""Bot interface"""
from abc import ABC, abstractmethod
from typing import List
from ..views import GameView
from ..actions import AvailableAction, Action
from ..simulator.types.identifiers import PlayerId


class BotInterface(ABC):
    """Interface that all bots must implement"""

    @abstractmethod
    def take_turn(
        self, view: GameView, available_actions: List[AvailableAction]
    ) -> Action:
        """
        Bot makes a decision.
        
        Args:
            view: Player-specific game view
            available_actions: List of legal actions
            
        Returns:
            An action chosen from available_actions
        """
        pass

    @abstractmethod
    def on_event(self, event: dict) -> None:
        """
        Receive a game event.
        
        Args:
            event: Game event notification
        """
        pass
