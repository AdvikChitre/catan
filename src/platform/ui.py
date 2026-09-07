"""Minimal browser UI mock for the Catan platform."""

UI_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Catan Platform Demo</title>
    <style>
      :root {
        --bg: #0f172a;
        --panel: #111827;
        --panel-2: #1f2937;
        --border: #334155;
        --blue: #60a5fa;
        --text: #e2e8f0;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      .layout {
        display: grid;
        grid-template-columns: 340px 1fr;
        min-height: 100vh;
      }
      .sidebar {
        background: #0b1120;
        border-right: 1px solid var(--border);
        padding: 20px;
      }
      .card {
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 18px;
      }
      .controls, .tabs {
        display: flex;
        gap: 10px;
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
        font-weight: 600;
      }
      button.secondary {
        background: #475569;
      }
      button.ghost {
        background: transparent;
        border: 1px solid var(--border);
      }
      main {
        padding: 24px;
      }
      .panel {
        background: #0b1220;
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 16px;
      }
      .board-wrap {
        overflow: auto;
        padding: 12px 0;
      }
      .board {
        position: relative;
        min-width: 650px;
        min-height: 500px;
        background: linear-gradient(135deg, #0b1321, #13273d);
        border: 2px solid var(--blue);
        border-radius: 18px;
        padding: 20px;
        display: grid;
        grid-template-columns: repeat(5, 120px);
        gap: 10px;
        place-content: center;
      }
      .tile {
        width: 110px;
        height: 92px;
        border-radius: 12px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        border: 2px solid rgba(255,255,255,0.18);
        font-weight: bold;
        box-shadow: inset 0 0 18px rgba(255,255,255,0.08);
      }
      .tile[data-type="wood"] { background: #166534; }
      .tile[data-type="brick"] { background: #b45309; }
      .tile[data-type="sheep"] { background: #4d7c0f; }
      .tile[data-type="wheat"] { background: #a16207; }
      .tile[data-type="ore"] { background: #374151; }
      .tile[data-type="desert"] { background: #6b7280; }
      .tile .token {
        width: 30px;
        height: 30px;
        border-radius: 50%;
        background: rgba(255,255,255,0.9);
        color: #111827;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 8px;
      }
      .status-grid {
        display: grid;
        grid-template-columns: repeat(2, minmax(140px, 1fr));
        gap: 10px;
      }
      .value {
        font-size: 1.2rem;
        font-weight: bold;
      }
      ul {
        list-style: none;
        padding: 0;
        margin: 0;
      }
      li {
        border-bottom: 1px solid var(--border);
        padding: 8px 0;
      }
      .muted { opacity: 0.75; }
      .hidden { display: none; }
    </style>
  </head>
  <body>
    <div class="layout">
      <aside class="sidebar">
        <div class="card">
          <h2>Room</h2>
          <div>Game ID: <span id="gameId" class="muted">not started</span></div>
          <div class="controls">
            <button id="createGameBtn">Create Demo Game</button>
            <button id="connectBtn" class="secondary">Connect</button>
          </div>
        </div>

        <div class="card">
          <h3>Players</h3>
          <ul id="playersList"></ul>
        </div>

        <div class="card">
          <h3>Event Feed</h3>
          <ul id="eventFeed"></ul>
        </div>
      </aside>

      <main>
        <div class="panel">
          <div class="tabs">
            <button id="liveTabBtn">Live</button>
            <button id="replayTabBtn" class="secondary">Replay</button>
          </div>

          <div id="livePanel">
            <div class="status-grid" style="margin-top: 18px;">
              <div class="card">
                <div class="muted">Current phase</div>
                <div id="phase" class="value">--</div>
              </div>
              <div class="card">
                <div class="muted">Turn</div>
                <div id="turn" class="value">--</div>
              </div>
              <div class="card">
                <div class="muted">Current player</div>
                <div id="currentPlayer" class="value">--</div>
              </div>
              <div class="card">
                <div class="muted">Winner</div>
                <div id="winner" class="value">--</div>
              </div>
            </div>

            <div class="board-wrap">
              <div id="board" class="board"></div>
            </div>
          </div>

          <div id="replayPanel" class="hidden">
            <div class="controls">
              <button id="loadReplayBtn">Load Replay</button>
              <button id="stepReplayBtn" class="secondary">Step</button>
              <button id="playReplayBtn" class="ghost">Play</button>
            </div>
            <div id="replaySummary" class="muted" style="margin-top: 14px;">No replay loaded.</div>
            <ul id="replayFeed" style="margin-top: 14px;"></ul>
          </div>
        </div>
      </main>
    </div>

    <script>
      const boardEl = document.getElementById('board');
      const eventFeedEl = document.getElementById('eventFeed');
      const replayFeedEl = document.getElementById('replayFeed');
      const playersListEl = document.getElementById('playersList');
      const gameIdEl = document.getElementById('gameId');
      const phaseEl = document.getElementById('phase');
      const turnEl = document.getElementById('turn');
      const currentPlayerEl = document.getElementById('currentPlayer');
      const winnerEl = document.getElementById('winner');
      const replaySummaryEl = document.getElementById('replaySummary');

      let currentGameId = null;
      let ws = null;
      let replayEvents = [];
      let replayIndex = 0;
      let replayTimer = null;

      const tileTemplates = [
        { type: 'wood', token: 4 }, { type: 'brick', token: 8 }, { type: 'sheep', token: 5 },
        { type: 'wheat', token: 6 }, { type: 'ore', token: 9 }, { type: 'desert', token: null },
        { type: 'wood', token: 10 }, { type: 'brick', token: 3 }, { type: 'sheep', token: 11 },
        { type: 'wheat', token: 2 }, { type: 'ore', token: 12 }, { type: 'wood', token: 9 },
        { type: 'brick', token: 5 }, { type: 'sheep', token: 6 }, { type: 'wheat', token: 8 },
        { type: 'ore', token: 10 }, { type: 'wood', token: 3 }, { type: 'brick', token: 11 },
        { type: 'sheep', token: 4 }
      ];

      function addEvent(msg) {
        const item = document.createElement('li');
        item.textContent = `${msg.type || 'event'}${msg.data ? ' :: ' + JSON.stringify(msg.data) : ''}`;
        eventFeedEl.prepend(item);
      }

      function renderBoard() {
        boardEl.innerHTML = '';
        tileTemplates.forEach((tile, index) => {
          const el = document.createElement('div');
          el.className = 'tile';
          el.dataset.type = tile.type;
          const token = document.createElement('div');
          token.className = 'token';
          token.textContent = tile.token ?? 'X';
          const label = document.createElement('div');
          label.textContent = tile.type.toUpperCase();
          el.appendChild(token);
          el.appendChild(label);
          boardEl.appendChild(el);
        });
      }

      function renderPlayers(players) {
        playersListEl.innerHTML = '';
        for (const player of players || []) {
          const item = document.createElement('li');
          item.textContent = `${player.player_id} - ${player.victory_points} VP`;
          playersListEl.appendChild(item);
        }
      }

      async function createGame() {
        const response = await fetch('/game/create', { method: 'POST' });
        const payload = await response.json();
        currentGameId = payload.game_id;
        gameIdEl.textContent = currentGameId;
        addEvent({ type: 'GameCreated', data: payload });
        await refreshState();
        connect();
      }

      async function refreshState() {
        if (!currentGameId) return;
        const response = await fetch(`/game/${currentGameId}/state`);
        const state = await response.json();
        phaseEl.textContent = state.phase || '--';
        turnEl.textContent = state.turn_number ?? '--';
        currentPlayerEl.textContent = state.current_player || '--';
        winnerEl.textContent = state.winner || '--';
        renderPlayers(state.players || []);
      }

      async function loadReplay() {
        if (!currentGameId) return;
        const response = await fetch(`/game/${currentGameId}/replay`);
        const replay = await response.json();
        replayEvents = replay.events || [];
        replayIndex = 0;
        replaySummaryEl.textContent = `Loaded ${replayEvents.length} events for ${currentGameId}`;
        replayFeedEl.innerHTML = '';
        for (const event of replayEvents.slice(0, 10)) {
          const item = document.createElement('li');
          item.textContent = `${event.sequence}: ${event.type}`;
          replayFeedEl.appendChild(item);
        }
      }

      function stepReplay() {
        if (!replayEvents.length) return;
        const event = replayEvents[replayIndex % replayEvents.length];
        const item = document.createElement('li');
        item.textContent = `${event.sequence}: ${event.type} :: ${JSON.stringify(event.data || {})}`;
        replayFeedEl.prepend(item);
        replayIndex += 1;
      }

      function playReplay() {
        if (!replayEvents.length) return;
        if (replayTimer) clearInterval(replayTimer);
        replayTimer = setInterval(() => {
          if (replayIndex >= replayEvents.length) {
            clearInterval(replayTimer);
            replayTimer = null;
            return;
          }
          stepReplay();
        }, 500);
      }

      function connect() {
        if (!currentGameId) return;
        if (ws) ws.close();
        ws = new WebSocket(`ws://localhost:8000/ws/game/${currentGameId}`);
        ws.onmessage = (event) => {
          const msg = JSON.parse(event.data);
          addEvent(msg);
          if (msg.type === 'SIMULATOR_COMPLETED') {
            refreshState();
          }
        };
      }

      document.getElementById('createGameBtn').addEventListener('click', createGame);
      document.getElementById('connectBtn').addEventListener('click', () => {
        if (currentGameId) connect();
      });
      document.getElementById('loadReplayBtn').addEventListener('click', loadReplay);
      document.getElementById('stepReplayBtn').addEventListener('click', stepReplay);
      document.getElementById('playReplayBtn').addEventListener('click', playReplay);

      document.getElementById('liveTabBtn').addEventListener('click', () => {
        document.getElementById('livePanel').classList.remove('hidden');
        document.getElementById('replayPanel').classList.add('hidden');
      });

      document.getElementById('replayTabBtn').addEventListener('click', () => {
        document.getElementById('replayPanel').classList.remove('hidden');
        document.getElementById('livePanel').classList.add('hidden');
      });

      renderBoard();
      renderPlayers([]);
    </script>
  </body>
</html>
"""
