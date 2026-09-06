"""Main entry point for the simulator"""
from __future__ import annotations

from typing import Any, List

from ..bots.bot_interface import BotInterface
from ..views import GameView
from ..simulator.types.identifiers import PlayerId
from ..simulation import Simulator


class DummyBot(BotInterface):
    """Simple deterministic bot for early simulation testing."""
    def on_game_start(self, view: GameView) -> None:
        """No-op at game start."""
        pass

    def take_turn(self, view: GameView, available_actions: List[Any]):
        """Return the first legal action or None if there are no choices."""
        if available_actions:
            return available_actions[0]
        return None

    def on_event(self, event: dict) -> None:
        """Receive a game event."""
        pass

    def on_game_end(self, result: Any) -> None:
        """No-op at game end."""
        pass


def main():
    """Run a complete game with dummy bots."""
    simulator = Simulator(seed=42)

    bots = {
        PlayerId.P1: DummyBot(),
        PlayerId.P2: DummyBot(),
        PlayerId.P3: DummyBot(),
        PlayerId.P4: DummyBot(),
    }
    simulator.register_bots(bots)

    print("Starting Catan simulator...")
    simulator.run()
    print("Game complete!")


if __name__ == "__main__":
    main()
