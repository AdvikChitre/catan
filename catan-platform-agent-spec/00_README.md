# Catan Bot Platform — Agent Implementation Specification

This is the implementation contract for the complete platform:

1. deterministic four-player Catan simulator
2. canonical versioned Bot API/SDK
3. bot wire protocol
4. isolated execution of uploaded user code
5. user bot storage/versioning
6. four-player rooms/lobbies
7. game workers
8. live WebSocket game stream
9. live web game viewer
10. persistent replay with timeline/time travel

Locked product vision:
- users can store multiple bot versions;
- upload new versions;
- create/join a four-player room;
- choose one owned BotVersion;
- click Ready;
- game starts when all four are ready with valid bots;
- actual simulator runs the game;
- browser shows the real game live from simulator events;
- finished games are replayable and scrubbable through history;
- users can inspect their own bot's decision/debug information where authorized.

Do not execute uploaded bot code inside the web/API server or simulator process.

Read all documents before coding. Follow `15_decision_log.md` for locked choices.
