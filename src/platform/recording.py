"""Public replay projection using native committed-transition observers."""
from __future__ import annotations

from collections import Counter
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
                     "victory_points": p.get_calculated_victory_points() if state.winner == p.player_id else
                     len(p.settlements) + 2 * len(p.cities) + 2 * int(p.has_longest_road) + 2 * int(p.has_largest_army),
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
EVENT_FIELDS.update({
    'GameStarted': ('seed', 'order'),
    'SettlementBuilt': ('vertex', 'setup'), 'RoadBuilt': ('edge', 'setup', 'free'),
    'CityBuilt': ('vertex',), 'ResourcesProduced': ('resources', 'setup'),
    'ResourcesTaken': ('resources',), 'CardsDiscarded': ('count',),
    'ResourceStolen': ('from_player', 'to_player'),
    'DevelopmentCardPlayed': ('card',), 'MonopolyResolved': ('resource', 'amounts'),
    'BankTradeCompleted': ('give', 'receive'),
    'TradeOffered': ('give', 'receive', 'recipients'),
    'TradeResponse': ('type', 'give', 'receive'),
    'TradeCompleted': ('responder', 'give', 'receive'), 'TradeCancelled': (),
    'AchievementChanged': ('achievement', 'owner'),
    'TurnStarted': ('player_id',), 'TurnEnded': (),
    'GameWon': ('winner', 'victory_points'),
    'GameEnded': ('status', 'reason', 'winner', 'turn_count', 'decisions', 'engine_version', 'protocol_version'),
})


class RecordingSimulator(Simulator):
    """Capture full public snapshots after engine transitions."""

    def begin_recording(self):
        self.frames = []
        self.public_events = []
        self._pending_events = []
        self.subscribe(self.capture)
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
        status = "failed" if error else ((self.result or {}).get("status", "stopped"))
        if status == "player_failed": status = "failed"
        rolls = Counter(str(e["data"]["total"]) for e in self.public_events
                        if e["type"] == "DiceRolled" and "total" in e["data"])
        production = Counter()
        for event in self.public_events:
            if event['type'] == 'ResourcesProduced':
                production[event['player_id']] += sum(event['data'].get('resources', {}).values())
        return {"schema_version": 1, "metadata": metadata, "geometry": geometry(self),
                "frames": self.frames, "events": self.public_events,
                "result": {"status": status, "winner": winner,
                           "reason": error or ("Victory recorded" if winner else
                             (self.result or {}).get("reason", "Recording captured before completion")),
                           "statistics": {"dice_rolls": dict(rolls), "roll_count": sum(rolls.values()),
                                          "recorded_transitions": len(self.frames) - 1,
                                          "resources_produced": dict(production),
                                          "player_trades": sum(e['type']=='TradeCompleted' for e in self.public_events),
                                          "bank_trades": sum(e['type']=='BankTradeCompleted' for e in self.public_events),
                                          "players": self.frames[-1]["state"]["players"]}}}

