"""Minimal browser UI mock for the Catan platform."""

UI_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Catan Platform Demo</title>
    <style>
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: #0f172a;
        color: #e2e8f0;
      }
      .layout {
        display: grid;
        grid-template-columns: 320px 1fr;
        min-height: 100vh;
      }
      .sidebar {
        background: #111827;
        padding: 24px;
        border-right: 1px solid #334155;
      }
      .card {
        background: #1f2937;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
      }
      .controls {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin-top: 12px;
      }
      button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 14px;
        cursor: pointer;
      }
      button.secondary {
        background: #475569;
      }
      main {
        padding: 24px;
      }
      .board {
        background: linear-gradient(135deg, #0b1321, #13273d);
        border: 2px solid #60a5fa;
        border-radius: 18px;
        padding: 20px;
        display: grid;
        grid-template-columns: repeat(5, 1fr);
        gap: 12px;
      }
      .tile {
        min-height: 96px;
        background: #14532d;
        border: 1px solid #86efac;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
      }
      .tile[data-type="brick"] { background: #b45309; }
      .tile[data-type="wood"] { background: #166534; }
      .tile[data-type="sheep"] { background: #4d7c0f; }
      .tile[data-type="wheat"] { background: #a16207; }
      .tile[data-type="ore"] { background: #374151; }
      #eventFeed {
        list-style: none;
        margin: 0;
        padding: 0;
      }
      #eventFeed li {
        border-bottom: 1px solid #334155;
        padding: 8px 0;
      }
    </style>
  </head>
  <body>
    <div class="layout">
      <aside class="sidebar">
        <div class="card">
          <h2>Room</h2>
          <div>Game ID: <span id="gameId">demo-game</span></div>
          <div class="controls">
            <button id="createGameBtn">Create Demo Game</button>
            <button id="connectBtn" class="secondary">Connect</button>
          </div>
        </div>

        <div class="card">
          <h3>Players</h3>
          <ul>
            <li>P1 — Alice</li>
            <li>P2 — Bot A</li>
            <li>P3 — Bot B</li>
            <li>P4 — Bot C</li>
          </ul>
        </div>

        <div class="card">
          <h3>Event Feed</h3>
          <ul id="eventFeed"></ul>
        </div>
      </aside>

      <main>
        <div class="card">
          <h2>Live Game</h2>
        </div>
        <div class="board" id="board">
          <div class="tile" data-type="wood">W</div>
          <div class="tile" data-type="brick">B</div>
          <div class="tile" data-type="sheep">S</div>
          <div class="tile" data-type="wheat">H</div>
          <div class="tile" data-type="ore">O</div>
          <div class="tile" data-type="wood">W</div>
          <div class="tile" data-type="brick">B</div>
          <div class="tile" data-type="wheat">H</div>
          <div class="tile" data-type="ore">O</div>
          <div class="tile" data-type="sheep">S</div>
          <div class="tile" data-type="sheep">S</div>
          <div class="tile" data-type="wheat">H</div>
          <div class="tile" data-type="ore">O</div>
          <div class="tile" data-type="wood">W</div>
          <div class="tile" data-type="brick">B</div>
        </div>
      </main>
    </div>

    <script>
      const eventFeed = document.getElementById('eventFeed');
      const gameIdLabel = document.getElementById('gameId');
      let ws = null;

      function addEvent(msg) {
        const item = document.createElement('li');
        item.textContent = `${msg.type || 'event'} ${msg.data ? JSON.stringify(msg.data) : ''}`.trim();
        eventFeed.prepend(item);
      }

      async function createGame() {
        const response = await fetch('/game/create', { method: 'POST' });
        const payload = await response.json();
        gameIdLabel.textContent = payload.game_id;
        addEvent({ type: 'GameCreated', data: payload });
        connect(payload.game_id);
      }

      function connect(gameId) {
        if (ws) {
          ws.close();
        }
        ws = new WebSocket(`ws://localhost:8000/ws/game/${gameId}`);
        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          addEvent(msg);
        };
      }

      document.getElementById('createGameBtn').addEventListener('click', createGame);
      document.getElementById('connectBtn').addEventListener('click', () => {
        const gameId = gameIdLabel.textContent.trim();
        if (gameId && gameId !== 'demo-game') {
          connect(gameId);
        }
      });
    </script>
  </body>
</html>
"""
