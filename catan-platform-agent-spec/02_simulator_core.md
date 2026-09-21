# 2. Simulator Core

The simulator is the authority.

## Owns
- GameState
- immutable BoardGeometry
- seeded RNG
- rules
- legal action generation
- bot decision calls via adapter
- state mutation
- events
- victory
- replay data

## Does not own
- accounts
- room state
- uploaded files
- browser rendering
- bot strategy

## Turn phases
- SETUP_FORWARD
- SETUP_REVERSE
- PRE_ROLL
- ROLL_REQUIRED
- ROBBER_DISCARD
- ROBBER_MOVE
- ROBBER_STEAL
- POST_ROLL
- TRADE_NEGOTIATION
- SPECIAL_ACTION
- GAME_OVER

## Bot direction
Simulator calls the bot. The bot returns a decision. The bot never mutates simulator state directly.

## GameView
Create a fresh player-specific immutable GameView for every bot decision.

## Actions
Concrete:
- BuildRoad(edge)
- BuildSettlement(vertex)
- BuildCity(vertex)

Umbrella:
- Trade
- complex special-card operations

Pre-roll:
- Roll
- PlayKnight if legal

## Rules in scope
Standard four-player Catan:
- board, resources, roads, settlements, cities, ports
- dice/production
- seven/discard/robber
- all standard development cards
- Longest Road
- Largest Army
- bank trading
- player trading
- counter-offers
- victory at 10 VP

## Standard costs
Road = 1 Brick + 1 Wood
Settlement = 1 Brick + 1 Wood + 1 Sheep + 1 Wheat
City = 3 Ore + 2 Wheat
Dev Card = 1 Sheep + 1 Wheat + 1 Ore

## Resource production
For each producing resource type on a non-7 roll:
1. calculate all player entitlements;
2. if the bank has fewer cards than the total required for that resource, nobody receives that resource this roll;
3. otherwise transfer all entitlements;
4. publish actual ResourcesReceived events.

## Trade
Trade is transactional. One final transaction can complete from each negotiation.
Counter-offers are allowed.
Transactions must validate both sides before changing anything.

## Determinism
One seeded RNG per game controls all random operations.

## Timeout/error defaults
3 seconds per gameplay decision.
Timeout, bot exception, malformed/invalid response -> bot forfeits.
