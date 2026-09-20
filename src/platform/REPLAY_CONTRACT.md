# Public replay format v1

`GET /games` lists saved job metadata. `POST /game/create?seed=42` launches a demo; room matches use `POST /rooms/{id}/start-game` with JSON `{ "seed": 42 }` after four valid bot selections and ready checks.

`GET /games/{id}` returns status and `replay_available`. A `queued` or `running` job has no readable replay yet. `GET /game/{id}/replay` returns HTTP 409 until saved, or 404 for an unknown ID. No live game stream is needed. Once ready, this returns:

```text
schema_version: 1
metadata:
  game_id, seed, room_id, players, participants
  status, created_at, started_at, finished_at, winner, reason, replay_available
geometry:
  valid_hex_topology
  tiles: [{id, x, y, vertices}]
  vertices: [{id, x, y}]
  edges: [{id, vertices: [a, b]}]
  ports: [{id, type, vertices: [a, b]}]
frames:
  - sequence: 0-based contiguous presentation position
    label: readable transition description
    events: public events belonging to this transition
    state:
      game_id, phase, turn_number, current_player, dice, winner
      tiles: {tile_id: {resource, number, robber}}
      buildings: {vertex_id: {owner, type}}
      roads: {edge_id: owner}
      players: [{player_id, victory_points, roads, settlements, cities,
                 knights, longest_road, largest_army}]
events: flattened public events
result:
  status, winner, reason
  statistics: {dice_rolls, roll_count, recorded_transitions, players}
```

All states are copied public snapshots. Position zero is the initial board. Each transition is a completed observed mutation boundary; nested actions are captured atomically at the outer boundary. Multiple simulator events can belong to one transition. Presentation sequence is distinct from the simulator's internal event sequence, which also contains private events. This avoids exposing private event gaps.

Full snapshots at each transition intentionally act as checkpoints everywhere for v1. The browser selects a frame directly. Compressing recordings later must preserve exact historical states and use a new schema version if the shape changes.

Only public piece-based points and achievements appear in `victory_points`; unrevealed VP cards and private hands are excluded. Unknown public event types keep their type but no payload until reviewed. No bot code, private GameView, raw GameState, private events, stdout or stderr is included. Anonymous `?player=P1` state queries return 403.

Status `stopped` means the simulator returned without a winner. `failed` means an error/interrupted job; a failed run may have a partial recording. `completed` requires a winner from the simulator. Neither the browser nor the worker invents victory. Results are withheld from the normal replay presentation until requested or the final frame is reached; this is spoiler avoidance, not access control.

Future valid geometry uses vertex display coordinates consistently across all tile corners and edge endpoints. The renderer sorts each tile's corners by angle; order in `vertices` is not significant. Tile axial coordinates are used for terrain-only fallback when the simulator geometry is not valid. Rendering never changes vertex/edge identities or simulator adjacency.


## Engine 2 integration

Schema 1 public snapshots remain compatible. New recordings have valid geometry and native transition observation. GameWon reveals the winning score; other hidden VP remain private. Events include production, trade negotiation, builds, cards and turn boundaries. Statistics additionally contain resources_produced by player, player_trades and bank_trades. A player_failed engine result maps to failed in the public match catalog.

The SQLite match_catalog stores job metadata; public .replay.json and restricted .audit.json are separate files. Only replay JSON is served by the HTTP API. Engine version, protocol version, configuration and implementation hashes identify a run. Legacy recordings remain readable without conversion.
