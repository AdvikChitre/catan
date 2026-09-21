# 10. Rooms and Lobby

A Room is a four-player lobby.

```ts
interface RoomPlayer {
  userId: string;
  seat: 1 | 2 | 3 | 4;
  selectedBotVersionId: string | null;
  ready: boolean;
}
```

Room states:
- WAITING
- READY_TO_START
- STARTING
- RUNNING
- FINISHED

Rules:
- maximum four players;
- one seat per user in a room;
- valid bot must be selected before Ready;
- changing bot selection clears Ready;
- all four players + valid bots + Ready => start.

When starting:
1. validate BotVersions again;
2. freeze seats and exact BotVersion IDs;
3. generate seed;
4. create Game;
5. launch worker.

Lobby live events:
- player joined/left
- bot selected
- ready changed
- game starting
- game started

Do not allow room changes to modify an existing Game.
