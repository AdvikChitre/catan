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
from .sandbox import SandboxedBotRunner, SandboxConfig


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
    use_sandbox: bool = False
    bot_code: Optional[str] = None
    sandbox_config: Optional[SandboxConfig] = None
    _sandboxed_runner: Optional[SandboxedBotRunner] = None

    def on_game_start(self, view: GameView) -> None:
        if self.use_sandbox and self._sandboxed_runner:
            self._sandboxed_runner.on_game_start(view)
        else:
            self.status = "playing"

    def take_turn(self, view: GameView, available_actions: List[Any]) -> Any:
        if self.use_sandbox and self._sandboxed_runner:
            return self._sandboxed_runner.take_turn(view, available_actions)
        if available_actions:
            return available_actions[0]
        return None

    def on_event(self, event: dict) -> None:
        if self.use_sandbox and self._sandboxed_runner:
            self._sandboxed_runner.on_event(event)
        return None

    def validate(self) -> Dict[str, Any]:
        """Validate the bot package or loaded bot adapter.

        This is intentionally lightweight: the platform can later replace it with
        package import / sandbox verification logic without changing callers.
        """
        self.last_error = None
        
        if self.use_sandbox and self.bot_code:
            # Create sandboxed runner for validation
            self._sandboxed_runner = SandboxedBotRunner(
                bot_id=self.bot_id,
                name=self.name,
                bot_code=self.bot_code,
                version=self.version,
                config=self.sandbox_config
            )
            validation_result = self._sandboxed_runner.validate()
            if validation_result.get("ok"):
                self.status = "ready"
                self.ready = True
            else:
                self.status = "invalid"
                self.last_error = validation_result.get("error")
                self.ready = False
            return validation_result
        else:
            # Non-sandboxed validation (for trusted bots)
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
        if self._sandboxed_runner:
            self._sandboxed_runner.cleanup()
        return {"bot_id": self.bot_id, "status": self.status}
