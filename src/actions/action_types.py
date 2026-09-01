"""Action types"""
from typing import Any


class Action:
    """Base action class"""
    pass


class AvailableAction:
    """Represents an available action for a bot"""
    def __init__(self, action_type: str, data: Any = None):
        self.action_type = action_type
        self.data = data
