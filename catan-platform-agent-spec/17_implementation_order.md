# 17. Implementation Order

## Phase 1 — Simulator
1. project skeleton
2. domain types
3. BoardGeometry
4. BoardState/GameState
5. seeded RNG
6. randomized board/deck
7. GameView privacy
8. events
9. setup
10. turn loop
11. building/action generation
12. robber
13. development cards
14. scoring/victory
15. trading
16. timeout/error handling
17. deterministic replay

## Phase 2 — Bot integration
18. canonical bot API
19. local SDK/template
20. JSONL wire protocol
21. local runner/protocol adapter
22. bot package validation
23. isolated production runner

## Phase 3 — Platform backend
24. users
25. bots/BotVersions
26. file/object storage
27. rooms/lobby
28. game registry/service
29. game workers

## Phase 4 — Live web
30. public API DTOs
31. WebSocket event streaming
32. public snapshots/reconnect
33. bot management UI
34. room UI
35. live game viewer

## Phase 5 — Replay
36. checkpoints
37. replay API
38. timeline controls
39. event/turn stepping
40. historical privacy filtering
41. authenticated own-bot debug viewer

## Phase 6 — Production hardening
42. authentication/authorization
43. upload quotas
44. rate limits
45. worker cleanup/recovery
46. sandbox hardening
47. monitoring/structured logs
48. backup/replay retention

## Rule
At every phase:
- implement;
- write tests;
- run full tests;
- preserve earlier API/contracts.

Do not move Catan rules into the browser.
Do not let browser connections block workers.
Do not run uploaded code in trusted server processes.
