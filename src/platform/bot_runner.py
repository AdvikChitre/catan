"""Bot runner abstraction for the platform layer.

This keeps the simulator independent from the local bot packaging system while
still providing a concrete interface the platform can use to manage uploaded
bot versions and bot readiness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..bots.bot_interface import BotInterface
from ..views import GameView


@dataclass
class BotRunner(BotInterface):
    """A platform-level wrapper around a bot implementation or bot package."""

    bot_id: str
    name: str
    version: str = "v1"
    status: str = "pending"
    ready: bool = False
    last_error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def on_game_start(self, view: GameView) -> None:
        self.status = "playing"

    def take_turn(self, view: GameView, available_actions: List[Any]) -> Any:
        if available_actions:
            return available_actions[0]
        return None

    def on_event(self, event: dict) -> None:
        return None

    def validate(self) -> Dict[str, Any]:
        """Validate the bot package or loaded bot adapter.

        This is intentionally lightweight: the platform can later replace it with
        package import / sandbox verification logic without changing callers.
        """
        self.last_error = None
        self.status = "ready"
        self.ready = True
        return {"ok": True, "bot_id": self.bot_id, "version": self.version}

    def start(self) -> Dict[str, Any]:
        """Start the bot runner for a game session."""
        if not self.ready:
            raise RuntimeError(f"Bot {self.bot_id} is not ready")
        self.status = "running"
        return {"bot_id": self.bot_id, "status": self.status}

    def stop(self) -> Dict[str, Any]:
        """Stop the bot runner."""
        self.status = "stopped"
        return {"bot_id": self.bot_id, "status": self.status}
