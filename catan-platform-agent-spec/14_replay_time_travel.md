# 14. Replay and Time Travel

Finished games must be fully inspectable.

## Replay structure
```text
Replay
├── metadata
├── initialPublicState
├── checkpoints
├── orderedEvents
└── finalResult
```

## Checkpoints
Store periodic public snapshots, e.g. every 100 events initially.
This is configurable.

To render sequence S:
1. load nearest checkpoint <= S;
2. apply events after checkpoint through S;
3. render resulting state.

## Controls
Provide:
- play/pause
- previous event
- next event
- previous turn
- next turn
- draggable timeline
- event/turn markers
- click-event-to-jump

## Historical privacy
At sequence S, render information visible at S.
Never use final state to reconstruct an earlier point.
Do not reveal another player's private resources/cards retroactively.

## Decision records
For every bot decision store privately:
- sequence
- player
- decision type
- available actions
- chosen response
- view/state hash and/or enough data for debug

For public replay, hide private decision context.

For authenticated player debug view, allow inspection of that user's own:
- GameView
- available actions
- chosen action
- bot logs
- private events

Never show another player's private decision data.

## Replay persistence
Replay survives worker shutdown.
