# Catan bot arena

A Python Catan simulator with a replay-first web interface: select four bots in a room, run the simulation in the background, then watch and inspect the saved recording independently.

## Start

```powershell
python -m pip install -r requirements.txt
python -m uvicorn src.platform.server:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Upload Player implementations, create a room, fill and ready all four seats, then simulate and watch the recorded match. See `DEPLOYMENT.md` for the Docker VPS setup.

The production frontend can be deployed independently through Vercel. See `VERCEL_DEPLOYMENT.md`; its build targets `https://catansim.duckdns.org` and the backend accepts explicitly configured frontend origins.

The simulator now runs full matches with real board topology, resource accounting, development cards, robber/discards, one-round trade negotiations and victory detection. Players implement `choose_action(view, options)` and a separate optional-no-op `on_event(event)`.

See [Player API](PLAYER_API.md), [Project structure and database](PROJECT_STRUCTURE.md), [Implementation plan](SIMULATOR_PLAN.md), and [Web interface guide](WEB_INTERFACE.md).

Run headlessly with `python -m src.simulator.run --seed 42 --replay match.json`. The web app also provides `/player-sdk.zip` with the player SDK and an example implementation.

## Tests

```powershell
python -m pytest -q
npm ci
npx playwright install chromium
npm run test:playback
npm run test:browser
```

Use one local server process. Accounts and secure execution of untrusted uploaded bots are not implemented yet.
