"""Bot manager"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from typing import Any, Dict, List

from ..simulator.types.identifiers import PlayerId
from .bot_interface import BotInterface


class BotManager:
    """Creates and manages exactly four bot instances."""
    def __init__(self, timeout_seconds: float = 1.0):
        self.bots: Dict[PlayerId, BotInterface] = {}
        self.timeout_seconds = timeout_seconds

    def register_bot(self, player_id: PlayerId, bot: BotInterface) -> None:
        """Register a bot for a player."""
        if not isinstance(bot, BotInterface):
            raise TypeError("Bot must implement BotInterface")
        self.bots[player_id] = bot

    def get_bot(self, player_id: PlayerId) -> BotInterface:
        """Get the bot for a player."""
        if player_id not in self.bots:
            raise KeyError(f"No bot registered for {player_id}")
        return self.bots[player_id]

    def get_all_bots(self) -> List[BotInterface]:
        """Return bots in canonical player order."""
        return [self.bots[player_id] for player_id in PlayerId.all_players() if player_id in self.bots]

    def call_bot(self, player_id: PlayerId, method_name: str, *args: Any, default: Any = None, fallback: Any = None, **kwargs: Any) -> Any:
        """Invoke a bot callback with timeout/error guarding and a safe fallback result."""
        bot = self.get_bot(player_id)
        method = getattr(bot, method_name, None)
        if method is None:
            return fallback if fallback is not None else default

        executor = ThreadPoolExecutor(max_workers=1)
        future = executor.submit(method, *args, **kwargs)
        try:
            return future.result(timeout=self.timeout_seconds)
        except (FutureTimeoutError, TimeoutError, OSError, ValueError, RuntimeError, TypeError):
            return fallback if fallback is not None else default
        except Exception:
            return fallback if fallback is not None else default
        finally:
            try:
                executor.shutdown(wait=False, cancel_futures=True)
            except TypeError:
                # Python versions without cancel_futures support
                executor.shutdown(wait=False)
