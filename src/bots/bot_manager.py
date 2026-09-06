"""Bot manager"""
from __future__ import annotations

from typing import Dict, List

from ..simulator.types.identifiers import PlayerId
from .bot_interface import BotInterface


class BotManager:
    """Creates and manages exactly four bot instances."""
    def __init__(self):
        self.bots: Dict[PlayerId, BotInterface] = {}

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
