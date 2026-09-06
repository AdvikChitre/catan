# 8. Rules and Transactions

## 8.1 Resource costs

Use standard Catan costs:

```text
Road:
    1 Brick
    1 Wood

Settlement:
    1 Brick
    1 Wood
    1 Sheep
    1 Wheat

City:
    3 Ore
    2 Wheat

Development Card:
    1 Sheep
    1 Wheat
    1 Ore
```

## 8.2 Settlement legality

Normal-game settlement:

1. vertex has no building;
2. every directly adjacent vertex has no building;
3. player has a road connected to that vertex, directly or through their road network;
4. player has a settlement piece remaining;
5. player can pay the cost.

Initial placement has its own setup rule and does not require an existing road network.

## 8.3 City legality

- target vertex contains own settlement;
- city piece remains;
- player can pay city cost.

Replace settlement with city.

## 8.4 Road legality

- edge is empty;
- player has road piece remaining;
- player has a valid connection according to road-network rules;
- player can pay road cost.

A player may connect through their own building/road.
An opponent settlement/city blocks through-connection as required by Catan rules.

## 8.5 Resource production

For roll N != 7:

For each tile with number token N and without robber:

1. inspect six surrounding vertices;
2. settlement owner receives 1;
3. city owner receives 2;
4. resource comes from bank;
5. if bank does not contain enough cards for a distribution, follow standard bank-availability rule: only available cards are distributed; do not create resources.

The implementation should centralize resource transfer in one function.

## 8.6 Bank trading

Default exchange ratio: 4:1.

A player can use a 3:1 port if they occupy either endpoint.

A player can use a 2:1 specific-resource port if they occupy either endpoint and give the required resource.

The simulator determines the best applicable legal ratio.

The bot chooses the concrete resource give/receive quantities.

## 8.7 Player trading

Player-to-player trades exchange resources only.

Development cards cannot be traded.

The active player creates an offer to one or more recipients.

An offer may request resources the proposer does not currently have, but the transaction cannot complete unless the final transaction is actually executable.

Recommended stricter behaviour: reject structurally invalid offers if the proposer cannot currently provide the offered resources. Use this stricter behaviour.

## 8.8 Trade transaction semantics

Initial offer:

```text
A -> [B,C]
give 2 sheep
receive 1 ore
```

Responses:

```text
B -> ACCEPT
C -> COUNTER
```

Then ask A to select a resolution.

At most one transaction completes.

The simulator revalidates the selected final transaction immediately before transfer.

If the proposer/responder no longer has required resources, the transaction fails without partial transfer.

Transfers must be atomic:

1. validate both sides;
2. subtract all give resources;
3. add all receive resources;
4. only then publish TradeCompleted.

Never perform one side of a trade and then discover the other side is invalid.

## 8.9 Knight

When played:

1. remove Knight from player's hand;
2. increment `knightsPlayed`;
3. recalculate Largest Army;
4. choose robber destination;
5. choose victim if possible;
6. randomly steal one card;
7. publish events.

A Knight can be played before rolling and after rolling subject to standard rules.

A player may not play more than one development card of the same active type in one action.

## 8.10 Road Building

Play the card.

Then request first legal road.

Execute it.

Recalculate legal options.

Then request second legal road.

If fewer than two legal roads exist, place as many as legally possible according to standard card semantics.

No resource cost.

## 8.11 Year of Plenty

Choose two resources.

Transfer available resources from bank subject to bank availability.

No opponent loses anything.

## 8.12 Monopoly

Choose one resource type.

For every opponent:

- take all cards of that type;
- transfer to current player.

Publish appropriate public event(s) without revealing private before/after totals beyond what a player could observe.

## 8.13 Victory Point cards

Victory Point cards remain private.

They count toward owner's score.

Do not make their identities public when purchased.

If a game win requires revealing hidden VP cards, reveal only the minimum required information in final game result/replay.

## 8.14 Longest Road

Recalculate after every road placement and after every building placement that can break another player's road.

Use the graph.

Do not rely on an increment-only counter.

The algorithm must handle branches, loops and opponent settlement blocking.

Award Longest Road to a player meeting the standard threshold and owning the longest qualifying road, subject to normal tie/ownership rules.

## 8.15 Largest Army

Track number of Knights played.

Use the standard threshold and transfer rules.

## 8.16 Victory

Use standard victory threshold: 10 victory points.

Check after:

- settlement;
- city;
- Longest Road change;
- Largest Army change;
- hidden VP becoming part of score;
- any other score-changing action.

## 8.17 Standard development-card purchase timing

A newly purchased development card may not be played immediately as part of the same turn's action sequence if standard Catan rules prohibit that card from being played on the purchase turn.

Enforce the standard rule that a newly bought development card cannot be played until a later turn.

Track purchase-turn metadata if necessary.

## 8.18 Trade plus build ordering

There is no artificial "two iterations" limit.

A player may perform any sequence of currently legal actions:

```text
Trade
Build Road
Trade
Build Settlement
Buy Dev Card
Trade
...
End Turn
```

The only restriction is what the standard rules and current state permit.
