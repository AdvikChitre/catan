# Replay-first web interface

The platform now follows **room → simulate → saved recording → watch independently**. There is no live game WebSocket. Room and job pages poll for status; playback reads a completed recording and does not rerun bots.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m uvicorn src.platform.server:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Python runs the application; Node is needed only for browser development/tests. Serve one API process for this local version (do not use multiple Uvicorn workers).

Enter a local player name, upload a Player version under My players, create or join a room, select a version and mark ready. Four ready seats enable **Simulate match**. The recording is available under Matches and from the room afterward.

Local player names are convenience identifiers, not authenticated accounts. This is a local development application, not a public service for untrusted uploads.

## What is implemented

- Match archive with queued/running/stopped/completed/failed status and reloadable links.
- Four-seat rooms, joining, persistent bot selections, ready/unready, selection resets, duplicate-seat/start protection and frozen participant/version metadata.
- Player-version creation, Python file/code upload, API validation diagnostics, details and duplicate-version protection. Every registered version contains a validated Player implementation.
- Background simulation in separate match processes supervised by a bounded two-thread pool, independent of browser lifetime.
- Atomic saved replay files and SQLite match metadata; restart recovery marks unfinished jobs as failed and retains completed recordings.
- Real recorded terrain, number tokens, robber, public player scores and achievements.
- A renderer for valid hex topology, roads, settlements, cities and ports. Older recordings with placeholder topology retain their labelled schematic; new games use the real hex board.
- Play/pause, speed, start/end, previous/next transition, previous/next turn, timeline drag, turn markers and journal jumps. Each viewer has independent playback state.
- Zoom, pan, reset, responsive layout, keyboard controls, error/empty states and downloadable replay JSON.
- Results shown on request or at the end: winner when recorded, termination reason, public piece/score totals and dice distribution.
- Public-only recordings and blocked anonymous private-state requests. Event payloads use an explicit allowlist, including removal of purchased development-card identity.

## Storage and boundaries

`CATAN_DB_URL` defaults to `sqlite:///catan_platform.db` for rooms, implementation versions and the match catalog. `CATAN_REPLAY_DIR` overrides the recording directory; by default it is the SQLite filename plus `.replays` (for example `catan_platform.db.replays`). Keep both across restarts. Local state is ignored by Git.

`src/platform/server.py` handles requests, starts jobs and serves the static client. `RecordingSimulator` in `src/platform/recording.py` subscribes to native committed simulator transitions. It does not replace rules or bot decisions. Every recorded transition contains a copied public snapshot, so random access and backward seeking are exact without client-side Catan rules. The final recording is written before metadata advertises that it is available.

The client lives in `src/platform/static/`: `app.js` handles screens, `board.js` draws SVG, and `playback.js` handles timeline navigation. The older embedded `ui.py` is no longer served; its prior working-tree edits were retained.

Public replay format is documented in `src/platform/REPLAY_CONTRACT.md`. Old metadata-only SQL game entries and old event-only logs do not contain enough data for this viewer and are not represented as playable recordings.

## Player execution and remaining hosting work

The complete simulator is described in [Player API](PLAYER_API.md) and [Project structure](PROJECT_STRUCTURE.md). Code uploads implement one persistent Player class; each seat gets a separate instance/process. Import, protocol, lifecycle and initial-decision smoke checks run during validation. Old script-protocol versions remain stored but need a new compatible implementation version to run.

Submitted players have callback, message and resource limits. This is still a trusted local application: authenticated ownership and filesystem/network isolation for public untrusted hosting are not implemented. Direct in-process players are trusted and unbounded; the web runner uses process execution.

Every engine transition invokes the recording observer. The client consumes snapshots and does not reproduce Catan rules. Public production and trading events are retained; private audit files are stored separately and are not downloadable through replay endpoints. The winner's total score is revealed at completion; other players' hidden cards remain excluded.

## Verify

```powershell
python -m pytest -q
npm ci
npx playwright install chromium
npm run test:playback
npm run test:browser
```

Browser tests start an isolated server on port 8011 with temporary storage. They cover playback and seeking, desktop/mobile layouts, independent viewers, a four-participant room, text escaping/error recovery, and a complete geometry fixture. The fixture is synthetic and used only to verify rendering; it is not presented as a simulator-generated game. Screenshots and traces are written under `test-results/`.
