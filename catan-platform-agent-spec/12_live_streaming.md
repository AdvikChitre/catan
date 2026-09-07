# 12. Live Streaming

Use HTTP for ordinary API queries and WebSocket for live game events.

## Subscription
When browser subscribes to GameId:
1. send current public snapshot;
2. send events after snapshot sequence;
3. send future events live.

## Sequence
Every public event has monotonically increasing logical sequence number.
Client tracks last sequence.

## Reconnect
Client can reconnect and request:
- events after last sequence, or
- newer snapshot + subsequent events.

## Backpressure
A slow browser must never slow the simulator.
Buffer/drop/disconnect spectator connections according to policy.

## Visibility
Public stream contains only public state/events.
A private player debugging channel requires authentication/authorization.

## Completion
Send GameEnded, then expose replay data.
