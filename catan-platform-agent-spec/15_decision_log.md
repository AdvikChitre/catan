# 15. Locked Decision Log

1. Four players only in v1.
2. Standard Catan only; no expansions.
3. Ports, robber and all standard dev cards included.
4. Simulator calculates VP, Longest Road and Largest Army.
5. Simulator owns game state.
6. Simulator calls bots; bots do not directly call state-mutating simulator methods.
7. Users upload untrusted code; production uses sandboxed bot runners.
8. Bots may keep arbitrary private memory for the game.
9. Fresh player-specific immutable GameView at every decision.
10. GameView contains no event history.
11. Observable events are delivered in real time through OnEvent.
12. Opponent resources/dev-card hands are hidden.
13. Resource receipt events are public.
14. Trade offers/counters are observable table events.
15. Trades are atomic transactions; one final trade can complete from a negotiation.
16. Simulator generates legal AvailableActions.
17. Builds are concrete available actions.
18. Trade is an umbrella action.
19. Complex card/robber choices use follow-up decision requests.
20. No artificial two-action trade/build limit.
21. Turn continues until EndTurn.
22. 3 seconds max per gameplay decision.
23. Same seed + same BotVersions => deterministic result/event stream.
24. Board = 54 vertices, 72 edges, 19 tiles.
25. Existing x/y coordinate system is public.
26. BoardGeometry immutable; BoardState mutable.
27. Simulator independent of web UI.
28. Users store multiple immutable BotVersions.
29. Games freeze exact BotVersion IDs.
30. Room starts only with four players, valid bot selections and all Ready.
31. Live UI consumes simulator public event stream.
32. Finished games are persistent replays.
33. Replay supports arbitrary time scrubbing and event/turn stepping.
34. Historical privacy must be preserved.
35. Bot template/SDK implements canonical interface.
36. Same bot contract works locally and through hosted runner.
37. v1 bot protocol is JSON-serializable; JSONL over stdin/stdout is recommended.
38. Bot stdout is protocol-only; diagnostics use stderr.
39. Default bot network access is disabled.
