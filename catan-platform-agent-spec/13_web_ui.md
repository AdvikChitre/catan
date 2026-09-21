# 13. Web UI

## Pages
- Home
- My Bots
- Bot upload + validation
- Room
- Live Game
- Replay Game

## My Bots
Show logical bots and immutable versions.
Provide:
- upload version
- validation status
- template download
- SDK documentation

## Upload
User chooses package.
Show validation result and errors.
Only valid versions are selectable.

## Room
Show four seats:
- user
- selected BotVersion
- Ready status

Disable game start until all four are valid/ready.

## Live Game
Board:
- 19 tiles
- numbers
- robber
- roads
- settlements/cities
- ports

Side panels:
- player names/bot versions
- public VP/achievements
- event feed

## Event feed
Show public events in order.
Examples:
- roll
- resource receipts
- build
- trades/counters
- robber
- development-card play
- victory

## UI architecture
Browser applies server events to public state.
Browser does not implement Catan legality/rules.

## Finished game
Show:
- winner
- bot versions
- seed/game metadata
- Replay button

## Responsive board
Board should support scaling/panning.
