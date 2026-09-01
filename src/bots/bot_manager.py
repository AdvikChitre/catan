"""Bot manager"""
from typing import Dict, List
from ..simulator.types.identifiers import PlayerId
from .bot_interface import BotInterface


class BotManager:
    """Creates and manages exactly four bot instances"""
    def __init__(self):
        self.bots: Dict[PlayerId, BotInterface] = {}

    def register_bot(self, player_id: PlayerId, bot: BotInterface) -> None:
        """Register a bot for a player"""
        self.bots[player_id] = bot

    def get_bot(self, player_id: PlayerId) -> BotInterface:
        """Get the bot for a player"""
        return self.bots[player_id]
