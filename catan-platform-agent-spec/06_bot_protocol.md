# 6. Bot Wire Protocol

Use a language-neutral JSON protocol.
Recommended version-1 transport: JSON Lines over stdin/stdout.

## Request
```json
{
  "requestId": "id",
  "type": "TAKE_TURN",
  "payload": {}
}
```

## Response
```json
{
  "requestId": "id",
  "type": "ACTION_RESPONSE",
  "payload": {
    "action": {}
  }
}
```

Events are one-way:
```json
{
  "type": "EVENT",
  "payload": {
    "event": {}
  }
}
```

Supported request kinds:
- GAME_START
- CHOOSE_INITIAL_PLACEMENT
- TAKE_TURN
- CREATE_TRADE_OFFER
- RESPOND_TO_TRADE
- CHOOSE_TRADE_OUTCOME
- CHOOSE_ROBBER_ACTION
- CHOOSE_ROAD_BUILDING
- CHOOSE_YEAR_OF_PLENTY
- CHOOSE_MONOPOLY
- CHOOSE_DISCARD
- GAME_END

## Rules
- requestId must be echoed in response;
- stdout is protocol-only;
- bot diagnostics go to stderr;
- malformed output = bot failure;
- protocol mismatch = reject before game;
- response timeout = bot failure;
- protocol must not alter game randomness.
