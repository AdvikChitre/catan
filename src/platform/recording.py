"""Public, self-contained recordings; no game rules or bot API changes."""
from __future__ import annotations

from collections import Counter
from functools import wraps
import json

from ..simulation import Simulator


def value(item):
    return getattr(item, "value", item)


def public_state(sim):
    state = sim.game_state
    board = state.board_state
    return {
        "game_id": state.game_id,
        "phase": value(state.phase),
        "turn_number": state.turn_state.turn_number,
        "current_player": value(state.turn_state.current_player),
        "dice": state.turn_state.dice_roll,
        "winner": value(state.winner),
        "tiles": {str(k): {"resource": value(t.resource_type) or "DESERT",
                            "number": t.number_token, "robber": t.has_robber}
                  for k, t in board.tiles.items()},
        "buildings": {str(k): {"owner": value(v.building.owner), "type": value(v.building.type)}
                      for k, v in board.vertices.items() if not v.building.is_empty()},
        "roads": {str(k): value(e.road.owner) for k, e in board.edges.items() if not e.road.is_empty()},
        "players": [{"player_id": value(p.player_id),
                     "victory_points": len(p.settlements) + 2 * len(p.cities)
                     + 2 * int(p.has_longest_road) + 2 * int(p.has_largest_army),
                     "roads": len(p.roads), "settlements": len(p.settlements), "cities": len(p.cities),
                     "knights": p.largest_army_count, "longest_road": p.has_longest_road,
                     "largest_army": p.has_largest_army} for p in state.players],
    }


def geometry(sim):
    g = sim.board_geometry
    # Geometry is exported faithfully, including existing simulator limitations.
    valid = all(len(t.vertex_ids) == 6 for t in g.tiles.values())
    valid = valid and len({tuple(sorted(e.vertex_ids)) for e in g.edges.values()}) == len(g.edges)
    return {
        "valid_hex_topology": valid,
        "tiles": [{"id": str(t.id), "x": t.coordinate.x, "y": t.coordinate.y,
                   "vertices": sorted(map(str, t.vertex_ids))} for t in g.tiles.values()],
        "vertices": [{"id": str(v.id), "x": v.coordinate.x, "y": v.coordinate.y}
                     for v in g.vertices.values()],
        "edges": [{"id": str(e.id), "vertices": sorted(map(str, e.vertex_ids))} for e in g.edges.values()],
        "ports": [{"id": str(p.id), "type": value(p.port_type), "vertices": sorted(map(str, p.vertex_ids))}
                  for p in g.ports.values()],
    }


# Unknown event payloads are intentionally omitted until reviewed for public use.
EVENT_FIELDS = {
    "GameStarted": ("seed", "player_id"),
    "SetupPlacement": ("player_id", "settlement_vertex_id", "road_edge_id", "vertex", "edge", "second_pass"),
    "InitialPlacement": ("player_id", "vertex", "edge"),
    "SetupPlacementMade": ("player_id", "settlement_vertex", "road_edge", "second_pass"),
    "DiceRolled": ("die1", "die2", "total"),
    "RobberMoved": ("tile_id", "player_id", "victim_id"),
    "DevelopmentCardPurchased": ("player_id",),
    "BankTrade": ("player_id", "give", "receive", "ratio"),
    "PlayerTrade": ("proposer", "responder", "give", "receive"),
    "GameEnded": ("winner",),
}


class RecordingSimulator(Simulator):
    """Observe completed method boundaries, including mutations without events.

    Frames are full public snapshots (a checkpoint at every transition). This
    favors correctness and arbitrary backward seeks over compression for v1.
    Nested mutations are captured once at their outer transaction boundary.
    """

    def begin_recording(self):
        self.frames = []
        self.public_events = []
        self._pending_events = []
        self._record_depth = 0
        self.event_bus.subscribe(self._observe_event)
        self.capture("Initial board")

    def _observe_event(self, event):
        if event.visibility != "PUBLIC":
            return
        payload = {key: value(event.data[key]) for key in EVENT_FIELDS.get(event.event_type, ())
                   if key in event.data}
        entry = {"sequence": len(self.public_events), "type": event.event_type,
                 "turn_number": event.turn_number, "player_id": value(event.player_id),
                 "data": payload, "visibility": "PUBLIC"}
        self.public_events.append(entry)
        self._pending_events.append(entry)

    def capture(self, label):
        snapshot = public_state(self)
        # Copy at capture time, not export time: history must never alias state.
        frame = json.loads(json.dumps({"sequence": len(self.frames), "label": label,
                                      "state": snapshot, "events": self._pending_events}))
        self._pending_events = []
        if self.frames and self.frames[-1]["state"] == snapshot and not frame["events"]:
            return
        self.frames.append(frame)

    def export_recording(self, metadata, error=None):
        self.capture("Run stopped" if not self.game_state.winner else "Game finished")
        winner = value(self.game_state.winner)
        status = "failed" if error else ("completed" if winner else "stopped")
        rolls = Counter(str(e["data"]["total"]) for e in self.public_events
                        if e["type"] == "DiceRolled" and "total" in e["data"])
        return {"schema_version": 1, "metadata": metadata, "geometry": geometry(self),
                "frames": self.frames, "events": self.public_events,
                "result": {"status": status, "winner": winner,
                           "reason": error or ("Victory recorded" if winner else
                             "Simulator returned without a winner. The current simulator runs eight turns."),
                           "statistics": {"dice_rolls": dict(rolls), "roll_count": sum(rolls.values()),
                                          "recorded_transitions": len(self.frames) - 1,
                                          "players": self.frames[-1]["state"]["players"]}}}


def recorded(method, label):
    @wraps(method)
    def call(self, *args, **kwargs):
        if not hasattr(self, "frames"):
            return method(self, *args, **kwargs)
        self._record_depth += 1
        succeeded = False
        try:
            result = method(self, *args, **kwargs)
            succeeded = True
            return result
        finally:
            self._record_depth -= 1
            if self._record_depth == 0 and succeeded:
                self.capture(label)
    return call


for _method, _label in {
    "start_game": "Game started", "_perform_setup_placement": "Initial placement",
    "roll_dice": "Dice rolled", "end_turn": "Next turn", "execute_action": "Action played",
    "move_robber": "Robber moved", "play_development_card": "Development card played",
    "bank_trade": "Bank trade", "player_trade": "Player trade",
    "buy_development_card": "Development card purchased",
}.items():
    setattr(RecordingSimulator, _method, recorded(getattr(Simulator, _method), _label))
