# 16. Testing and Acceptance

## Simulator
Test:
- board counts/adjacency
- deterministic setup
- resource conservation
- production
- all building rules
- ports
- robber/discard/steal
- all development cards
- Longest Road
- Largest Army
- victory
- trade/counter-offer atomicity
- GameView privacy
- event visibility/order
- timeout/error handling
- deterministic replay

## Bot SDK/protocol
Test:
- template starts
- all methods accessible
- DTO serialization
- valid/invalid actions
- request/response IDs
- event delivery
- SDK/protocol compatibility

## Upload validation
Test valid package, missing manifest, invalid entrypoint, missing interface, incompatible versions, bad paths, oversized package, crashing bot.

## Sandbox security
Use dedicated security tests for:
- host filesystem access
- network
- environment secrets
- other bot workspace/process
- CPU exhaustion
- memory exhaustion
- process spawning
- filesystem traversal

## Rooms
Test:
- max four
- bot selection
- Ready gating
- selection clears Ready
- start when four are valid/ready
- exact versions frozen

## Live stream
Test:
- snapshot
- ordered events
- reconnect
- missed-event catch-up
- slow clients not blocking worker

## UI
Test:
- room updates
- bot upload/validation
- live board updates
- event feed
- privacy
- replay open
- arbitrary scrubbing
- previous/next event
- previous/next turn
- reconnect

## End-to-end
1. create four test users;
2. create/upload four bots;
3. join same room;
4. select bots;
5. Ready all;
6. game starts;
7. live events arrive;
8. game finishes;
9. replay opens;
10. scrub beginning -> end;
11. verify winner/final state.

## Acceptance
A real user must be able to complete the full workflow without manual server intervention.
