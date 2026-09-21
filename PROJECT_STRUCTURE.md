# Project structure

```text
Browser (HTML/CSS/JavaScript)
    | HTTP: rooms, implementations, jobs, completed replay
FastAPI backend (src/platform/server.py)
    |                 |
    |                 +-- SQLite: rooms, seats, implementation versions, match catalog
    |
    +-- bounded job supervisors --> one match worker process
                                     |
                                     +-- Simulator (src/simulation)
                                     |     +-- Rules (src/rules)
                                     |     +-- Board + authoritative state (src/board, src/core)
                                     |     +-- Player observations (src/views)
                                     |     +-- Ordered events (src/events)
                                     |
                                     +-- four persistent Player instances/processes
                                     |
                                     +-- public replay JSON + private audit JSON
Browser downloads public replay and plays it independently
```

The frontend lives in `src/platform/static`: `app.js` manages screens and HTTP requests, `board.js` renders the board, and `playback.js` navigates recorded frames. It has no Catan rule implementation and never makes decisions for players. Rooms and jobs poll for status. Watching does not rerun the match or require player processes to remain alive.

The backend is a Python FastAPI application served by Uvicorn. It validates room readiness, freezes exact implementation versions/hashes, creates a job, launches a worker and serves the completed recording. Two supervisor threads allow up to two concurrent match processes; actual simulation runs outside the API process. Use one API instance for this local deployment.

`src/platform/match_worker.py` loads the selected implementations, constructs a simulator, runs it and saves outputs. Each submitted class is hosted by `src/player/host.py` in its own persistent process through `ProcessPlayer`. The built-in example runs directly inside the match worker. The standalone engine imports neither FastAPI nor SQLAlchemy and can run without the website or a database.

`src/simulation/simulator.py` owns game lifecycle, pending decisions and event delivery. `src/rules/rules_engine.py` owns option generation, validation, transfers, rule effects and scoring. The engine is the only source of truth for a running game. Geometry is separate from mutable board state. The public SDK is `src/player`; observations contain copies, never mutable engine objects.

## What the database is for

The default database is `catan_platform.db` (SQLite, accessed through SQLAlchemy for room/implementation records and SQLite transactions for the match catalog):

- Rooms, participant names, seat assignments, selected implementation versions and readiness.
- Uploaded source, version names, descriptions and validation status.
- `match_catalog`: job status, participants, exact version hashes, seed, result and recording availability.

The older schema also contains `users` and `games` tables. Their presence does not mean authentication exists. The current app uses local display names, and `match_catalog` is authoritative for replay jobs. The older metadata service is retained for compatibility, not called by the live server.

Actual resources, roads and turn state stay in memory while a match runs; the database does not execute or validate game moves. Full public recordings are JSON files in `catan_platform.db.replays` by default. Separate `.audit.json` files contain private decisions/events and are never served by replay endpoints. Keep both the database and replay directory when backing up.

Legacy `.meta.json` records are imported into the catalog without deleting the original files or recordings. Startup reconciles interrupted jobs: completed recordings remain available; unfinished computation is marked failed rather than resumed from an arbitrary partial state.

`CATAN_DB_URL` selects the room/implementation database. With a SQLite URL, the match catalog shares that database; with another supported SQLAlchemy URL, the local catalog remains in the replay directory. `CATAN_REPLAY_DIR` overrides the recording directory. Public production hosting, authenticated ownership and hostile-code isolation remain separate deployment work.
