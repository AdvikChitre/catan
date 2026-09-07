# 9. Users, Bots and Versions

## User
Owns logical bots.

## Bot
Logical identity, e.g. `AggressiveBot`.

## BotVersion
Immutable uploaded implementation.

```text
id
botId
version
language
sdkVersion
protocolVersion
artifactLocation
validationStatus
createdAt
```

## UI
My Bots page lists:
- logical bot names
- versions
- valid/invalid status
- validation diagnostics
- upload-new-version action

## Game reference
Game stores exact BotVersion IDs.
Never use "latest version" when resolving a game.

## Ownership
By default a user can select only their own BotVersions.
Sharing can be added later.
