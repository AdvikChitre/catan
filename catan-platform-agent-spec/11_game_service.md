# 11. Game Service and Workers

## Game metadata
Store:
- gameId
- roomId
- seed
- players/seats
- BotVersion IDs
- created/started/finished times
- winner
- termination reason
- replay location

## Worker lifecycle
CREATED -> STARTING -> RUNNING -> FINISHED
Possible failure states: FAILED, CANCELLED.

## Worker
The Game Worker:
- starts simulator;
- starts four bot runners;
- runs game;
- sends public events;
- saves final result;
- saves replay/checkpoints.

Web/API handlers must not mutate live simulator state.

## Multiple games
Support multiple workers simultaneously.
Never keep live simulator state in a global singleton.

## Browser disconnect
Games continue running when spectators disconnect.
