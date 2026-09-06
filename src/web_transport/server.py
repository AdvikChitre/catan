"""Minimal web transport helpers (stdlib-friendly).

Provides simple functions that return JSON-serializable dicts for:
- replay export: `/game/{id}/replay`
- game state for a player: `/game/{id}/state?player=P1`

This module is intentionally small and dependency-free so it can be embedded into
multiple server frameworks later (Flask/FastAPI) by wrapping these helpers.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from ..simulation import Simulator
from ..simulator.types.identifiers import PlayerId


def get_replay(sim: Simulator) -> Dict[str, Any]:
    """Return the replay export for the simulator as a JSON-serializable dict."""
    if not hasattr(sim, "replay_recorder"):
        return {"metadata": {}, "events": []}
    return sim.replay_recorder.export()


def get_state(sim: Simulator, player_id: Optional[PlayerId] = None) -> Dict[str, Any]:
    """Return a JSON-serializable game state snapshot.

    If `player_id` is provided, return the `GameView` for that player; otherwise
    return a public summary of the game state.
    """
    if player_id is None:
        # public summary
        return {
            "game_id": sim.game_state.game_id,
            "phase": sim.game_state.phase,
            "turn_number": sim.game_state.turn_state.turn_number,
            "current_player": sim.game_state.turn_state.current_player.value,
            "players": [
                {
                    "player_id": p.player_id.value,
                    "victory_points": p.victory_points,
                }
                for p in sim.game_state.players
            ],
        }

    # per-player view
    view = sim.build_view_for_player(player_id)
    # Convert GameView into a JSON-friendly dict
    resources = {k.value: v for k, v in getattr(view.self, "resources", {}).items()}
    tiles = [
        {
            "tile_id": t.tile_id,
            "resource": t.resource_type.value if t.resource_type is not None else None,
            "number_token": t.number_token,
            "has_robber": t.has_robber,
        }
        for t in getattr(view, "board", []).tiles
    ]

    return {
        "player_id": player_id.value,
        "resources": resources,
        "victory_points": getattr(view.self, "victory_points", None),
        "board": {"tiles": tiles},
    }
