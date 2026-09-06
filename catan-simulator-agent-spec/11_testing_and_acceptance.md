# 11. Testing and Acceptance

The implementation is complete only when all categories below pass.

## 11.1 Geometry tests

Verify:

- exactly 19 tiles;
- exactly 54 vertices;
- exactly 72 edges;
- every tile has 6 vertices;
- every edge has 2 distinct endpoints;
- all vertex/edge/tile references are valid;
- no duplicate edge;
- coordinate equality works;
- port endpoints are valid;
- robber starts on desert.

## 11.2 Setup tests

Verify:

- player order P1-P4;
- snake order P1 P2 P3 P4 P4 P3 P2 P1;
- every placement is legal;
- each player gets correct starting pieces/resources;
- setup ends in P1 PRE_ROLL;
- seeded setup is reproducible.

## 11.3 Resource tests

Verify:

- all player resource counts never become negative;
- bank and player resource totals are conserved;
- settlement produces 1;
- city produces 2;
- robber blocks tile production;
- 7 does not produce;
- insufficient bank resources do not create cards from nowhere.

## 11.4 Building tests

Verify:

- roads require cost and legal connection;
- settlements enforce distance rule;
- cities only replace own settlement;
- piece supply is enforced;
- resource cost is applied exactly once;
- state and events agree.

## 11.5 Port tests

Test:

- 4:1 bank trade;
- 3:1 port;
- each specific 2:1 port;
- port access from either endpoint;
- city also grants port access.

## 11.6 Robber tests

Verify:

- destination is a valid tile;
- cannot remain on the same tile;
- only eligible adjacent victims can be selected;
- stolen resource is selected by simulator RNG;
- no-resource victim cannot be selected;
- exact stolen count is one card.

## 11.7 Development card tests

Test every card type.

Verify:

- deck count;
- card distribution;
- hidden identity after purchase;
- cannot play newly bought card if standard timing forbids it;
- Knight updates Largest Army;
- Road Building placement;
- Year of Plenty;
- Monopoly;
- Victory Point scoring.

## 11.8 Longest Road tests

Create fixed board scenarios covering:

- straight path;
- branch;
- loop;
- path broken by opponent settlement;
- ties;
- ownership transfer;
- placement that changes another player's longest road.

## 11.9 Largest Army tests

Verify:

- threshold;
- ownership;
- ties;
- transfer after Knight play.

## 11.10 Trade tests

Test:

- successful trade;
- rejection;
- counter-offer;
- multiple recipients;
- multiple accepts;
- proposer selects one final response;
- selected responder lacks resources;
- proposer lacks resources;
- atomic failure;
- no development-card trading;
- bank trading ratios.

## 11.11 Visibility tests

Create an internal game state with known hidden values.

Verify:

- Player 1 sees own resources;
- Player 1 does not see Player 2/3/4 resources;
- Player 1 sees own development cards;
- Player 1 does not see opponent development cards;
- public board state is visible;
- ResourceReceived events are visible;
- hidden card identity is not leaked;
- private robber steal information is filtered correctly;
- GameView contains no event history.

## 11.12 Event tests

Verify:

- every required event is generated;
- state changes happen before event delivery;
- sequence numbers strictly increase;
- public/private visibility is correct;
- bots receive only allowed events.

## 11.13 Bot lifecycle tests

Use a deterministic dummy bot that:

- always selects first available action;
- records OnEvent calls;
- never accesses simulator directly.

Verify it can complete simple controlled games.

## 11.14 Timeout tests

Use a test bot that sleeps longer than 3 seconds.

Verify:

- game terminates;
- correct bot is identified;
- no deadlock;
- result says BOT_TIMEOUT.

## 11.15 Exception tests

Use a bot that throws from every decision method.

Verify clean forfeit and no corrupted state.

## 11.16 Replay determinism

Run identical game twice with the same:

- seed;
- board configuration;
- bot implementations;
- bot configuration.

Require identical:

- final result;
- event sequence;
- event payloads;
- game progression.

## 11.17 State invariant tests

During development, repeatedly assert:

- no negative resources;
- no negative bank;
- card conservation;
- no duplicate building;
- no duplicate road;
- correct piece counts;
- exactly one robber;
- four players exist;
- current player is valid.

## 11.18 Acceptance criteria

The implementation is accepted when:

1. A complete four-player game can run to victory.
2. Two different bot implementations can compete without simulator changes.
3. Bots cannot access hidden information through public API objects.
4. Bots can maintain private memory via normal object fields.
5. AvailableActions contain only legal current actions.
6. Trades support counter-offers and transactional resolution.
7. All standard rules in scope are implemented.
8. Same seed + same bots produce same result/event stream.
9. A broken or slow bot cannot hang the simulation indefinitely.
10. A separate web client can visualize a game from simulator outputs.
