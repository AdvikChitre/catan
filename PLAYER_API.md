# Player API, protocol version 1

Implement one Python class derived from `src.player.Player`. One instance lives for the whole match, independently for each seat. Do not implement JSON transport yourself; the SDK host handles it. Uploads must be trusted local code: resource/process limits are implemented, but filesystem and network access are not isolated.

```python
from src.player import Player

class MyPlayer(Player):
    def on_game_start(self, view):
        self.production = {}

    def on_event(self, event):
        if event.type == 'ResourcesProduced':
            for resource, count in event.data.resources.items():
                key = (event.player_id, resource)
                self.production[key] = self.production.get(key, 0) + count

    def choose_action(self, view, options):
        # This is only a sketch: Discard and Trade require filled-in fields.
        return options[0]

    def on_game_end(self, result):
        pass
```

Use `examples/my_player.py` for a complete runnable baseline that handles all decisions. `src/player/example.py` contains its simple deterministic strategy. Neither is intended as a competitive strategy.

## Methods and ordering

- `choose_action(view, options)` is the only decision method and must be overridden.
- `on_event(event)` is invoked separately for every visible event. The default is a no-op. Its return value is ignored.
- `on_game_start(view)` and `on_game_end(result)` are optional no-op lifecycle hooks.
- After a legal action, the engine commits the change, publishes its ordered events, finishes delivering them to all eligible players, then asks for the next decision.
- No methods run concurrently on the same player. Your callbacks may update your own memory, but cannot act on the game except by returning an action from `choose_action`.
- Trade responses and discards may require a decision during another player's turn. `view.player_id` is always your identity; `view.turn.current_player` is the owner of the turn.
- Final events are delivered before `on_game_end`. A callback failure is recorded; already committed changes are not rolled back because a listener failed.

Views, options and events are detached immutable mappings with attribute access. Nested sequences are tuples. `value['key']` and `value.key` both work. Use `src.player.thaw(value)` to create a mutable ordinary dict/list copy. All public IDs and enum values are strings, identical locally and through the process adapter.

## Observation

`view` contains:

- `protocol_version`, `game_id`, `player_id`, `decision_id`.
- `self`: own resource/development-card maps; newly purchased development cards; piece supplies; resource/card counts; knights; achievements; total own score.
- `opponents`: public resource/card counts, piece supplies, played knights, achievements and public scores. No hidden card identities or resource maps.
- `board.tiles`: resource, number, robber flag, surrounding vertex/edge IDs.
- `board.vertices`: coordinates, neighboring vertices, edges, tiles, port, owner and building type.
- `board.edges`: endpoints and owner; `board.ports`: type and endpoints; `board.robber_tile`.
- `bank`: remaining resource counts; `development_deck_count`: remaining deck size, never order or composition.
- `turn`: `number`, `current_player`, `game_phase`, decision `phase`, and dice total if rolled.
- `trade`: pending proposal and eligible agreements, or null.

Resource names: `WOOD`, `BRICK`, `SHEEP`, `WHEAT`, `ORE`. Development cards: `KNIGHT`, `ROAD_BUILDING`, `YEAR_OF_PLENTY`, `MONOPOLY`, `VICTORY_POINT`.

The game seed is not sent to players because it would disclose future random outcomes. It is saved in the finished recording and private audit. There is no raw `GameState` in a view.

## Actions

Usually return one of `options` unchanged. Locations and resource combinations are concrete legal choices, refreshed after every action. Only `TRADE`, `COUNTER` and `DISCARD` are templates you fill in. Extra fields and unavailable actions are rejected.

| Type | Fields / meaning |
|---|---|
| `PLACE_SETTLEMENT` | `vertex`; initial setup |
| `PLACE_ROAD` | `edge`; road adjoining the just-placed settlement |
| `ROLL` | Mandatory before post-roll actions |
| `BUILD_ROAD` | `edge` |
| `BUILD_SETTLEMENT` | `vertex` |
| `BUILD_CITY` | `vertex`; replaces own settlement |
| `BUY_DEVELOPMENT_CARD` | Draws one hidden card |
| `PLAY_DEVELOPMENT_CARD` | `card`; enters another decision context |
| `MOVE_ROBBER` | `tile`, `victim` (player ID or null) |
| `BUILD_FREE_ROAD` | `edge`; Road Building calls this up to twice, recalculating legality |
| `TAKE_RESOURCES` | `resources` map; offered Year of Plenty choices |
| `TAKE_MONOPOLY` | `resource` |
| `BANK_TRADE` | `give_resource`, `receive_resource`, `ratio`; ratio computed by engine |
| `TRADE` | Player fills `recipients`, `give`, `receive` |
| `ACCEPT`, `REJECT` | Response to the current original offer |
| `COUNTER` | Responder fills `give`, `receive` from their own perspective |
| `SELECT_TRADE` | `response`; index into `view.trade.responses` |
| `CANCEL_TRADE` | Completes negotiation without transfer |
| `DISCARD` | Option supplies `count`; return `resources` with exactly that total, omitting `count` |
| `END_TURN` | Available only after required turn decisions finish |

Example proposal:

```python
return {
    'type': 'TRADE',
    'recipients': ['P2', 'P3'],
    'give': {'WOOD': 2},
    'receive': {'ORE': 1},
}
```

The simulator offers only `{'type': 'TRADE'}`; it never enumerates proposals. Give/receive maps must be nonempty positive integer amounts with no resource on both sides. You must hold your offered cards. Recipients are distinct other players. They respond in seat-ID order, once each; everyone sees the proposal and responses. A counter is from the responder's perspective. Final response entries normalize give/receive back to the proposer's perspective. The proposer chooses one executable agreement or cancels. The simulator revalidates both hands before transferring. No recursive counter round; a new proposal is allowed afterward.

Discard example: `{'type': 'DISCARD', 'resources': {'WOOD': 2, 'SHEEP': 1}}` when the offered count is three.

## Events

An event contains `sequence`, `type`, `player_id`, `turn_number`, and `data`. Global sequence gaps are expected when private events are omitted. Event data is described by the emitting operation:

| Events | Data |
|---|---|
| `GameStarted` | clockwise seat order |
| `TurnStarted`, `TurnEnded` | turn owner in event `player_id` |
| `DiceRolled` | `die1`, `die2`, `total` |
| `ResourcesProduced` | exact `resources` map; optional `setup` |
| `SettlementBuilt`, `CityBuilt`, `RoadBuilt` | `vertex` or `edge`; optional `setup` / `free` |
| `TradeOffered`, `TradeResponse`, `TradeCompleted`, `TradeCancelled` | proposal/response data or completed exchange |
| `BankTradeCompleted` | `give`, `receive` |
| `DevelopmentCardPurchased` | occurrence only; no identity |
| `DevelopmentCardPlayed` | public `card` |
| `ResourcesTaken`, `MonopolyResolved` | resource selection / per-player amounts |
| `CardsDiscarded` | public `count` only |
| `RobberMoved`, `ResourceStolen` | destination/victim; theft participants |
| `AchievementChanged` | achievement and new owner or null |
| `GameWon`, `GameEnded` | winner/revealed winning score and result |
| Private `DevelopmentCardDrawn`, `DiscardDetails`, `TheftDetails` | own draw, own discard, stolen-card identity for thief and victim |

You may ignore events or maintain any inference model you like. Opponent hand contents are never supplied directly. The public replay reveals the winner's score at completion; other hidden VP remain private.

## Running and validating

```powershell
python -m src.simulator.run --seed 42 --replay match.json
python -m src.simulator.run --seed 42 --player examples/my_player.py --player examples/my_player.py --player examples/my_player.py --player examples/my_player.py --replay match.json
```

Zero `--player` arguments use four example players. Four files use persistent processes. `--max-turns` overrides the default 1000-turn limit. `--audit private-audit.json` saves private decisions/events for local debugging; never publish that file as a replay.

The web upload verifies import, one subclass, protocol version, construction, lifecycle/event handling and an initial legal decision. This smoke test cannot prove the strategy handles every later situation.

Process callbacks default to a two-second limit. Messages are limited to 2 MB and diagnostic retention to 16 KB. Windows Job Objects cap each submitted player at one process, 256 MB combined memory and 30 seconds of CPU over its lifetime; closing the job kills its process tree. POSIX uses process groups and resource limits. The platform also caps each match at 180 seconds. These local execution limits are not network/filesystem security.

Invalid decisions or callback failures end competitive matches with `player_failed` (shown as failed in the web catalog); no silent replacement strategy is used. Operational limits produce `stopped`, not a winner. Direct in-process execution is for trusted code and does not enforce callback timeouts.

Old `take_turn` / per-card callbacks and the former input-file script protocol are incompatible. Existing files/versions are preserved, but authors must submit a new version implementing this API.
