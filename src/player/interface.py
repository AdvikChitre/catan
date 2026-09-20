"""The stable Python player contract and immutable JSON-compatible values."""
from collections.abc import Mapping
from enum import Enum

PROTOCOL_VERSION = 1


class FrozenMap(Mapping):
    """Read-only snapshot supporting both mapping and attribute access."""
    __slots__ = ("__data",)

    def __init__(self, values):
        object.__setattr__(self, "_FrozenMap__data", {k: freeze(v) for k, v in values.items()})

    def __getitem__(self, key):
        return self.__data[key]

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as error:
            raise AttributeError(key) from error

    def __setattr__(self, key, value):
        raise TypeError("Snapshots are read-only")


def freeze(value):
    if isinstance(value, Mapping):
        return FrozenMap(value)
    if isinstance(value, (tuple, list)):
        return tuple(freeze(v) for v in value)
    if isinstance(value, Enum):
        return value.value
    return value


def thaw(value):
    if isinstance(value, Mapping):
        return {k: thaw(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [thaw(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    return value


class Player:
    """One instance per seat. Only choose_action must be overridden.

    Return one offered action, or fill the documented fields of a constrained
    action (Trade, Counter or Discard). The engine owns validation and rules.
    on_event completes before the next choice and never returns an action.
    """
    protocol_version = PROTOCOL_VERSION

    def on_game_start(self, view):
        pass

    def on_event(self, event):
        pass

    def choose_action(self, view, options):
        raise NotImplementedError

    def on_game_end(self, result):
        pass
