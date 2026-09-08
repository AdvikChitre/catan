"""Enhanced browser UI for the Catan platform with bot management."""

UI_HTML = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Catan Platform</title>
    <style>
      :root {
        --bg: #0f172a;
        --panel: #111827;
        --panel-2: #1f2937;
        --border: #334155;
        --blue: #60a5fa;
        --green: #10b981;
        --red: #ef4444;
        --text: #e2e8f0;
      }
      * { box-sizing: border-box; }
      body {
        margin: 0;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
        background: var(--bg);
        color: var(--text);
      }
      .layout {
        display: grid;
        grid-template-columns: 250px 1fr;
        min-height: 100vh;
      }
      .sidebar {
        background: #0b1120;
        border-right: 1px solid var(--border);
        padding: 16px;
      }
      .nav-item {
        padding: 12px 16px;
        margin: 4px 0;
        border-radius: 8px;
        cursor: pointer;
        transition: background 0.2s;
        font-weight: 500;
      }
      .nav-item:hover {
        background: var(--panel-2);
      }
      .nav-item.active {
        background: var(--blue);
        color: white;
      }
      .card {
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 16px;
      }
      .controls, .tabs {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin-top: 12px;
      }
      button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 8px 12px;
        cursor: pointer;
        font-weight: 500;
        font-size: 14px;
      }
      button:hover {
        background: #1d4ed8;
      }
      button.secondary {
        background: #475569;
      }
      button.secondary:hover {
        background: #374151;
      }
      button.ghost {
        background: transparent;
        border: 1px solid var(--border);
      }
      button.ghost:hover {
        background: var(--panel-2);
      }
      button.danger {
        background: var(--red);
      }
      button.danger:hover {
        background: #dc2626;
      }
      main {
        padding: 24px;
      }
      .panel {
        background: #0b1220;
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 20px;
      }
      .status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 12px;
        margin: 16px 0;
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
        padding: 10px 0;
      }
      .muted { opacity: 0.75; }
      .hidden { display: none; }
      
      /* Form styles */
      .form-group {
        margin-bottom: 16px;
      }
      label {
        display: block;
        margin-bottom: 6px;
        font-weight: 500;
      }
      input, textarea, select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid var(--border);
        border-radius: 6px;
        background: var(--panel);
        color: var(--text);
        font-size: 14px;
      }
      textarea {
        resize: vertical;
        min-height: 100px;
        font-family: 'Courier New', monospace;
      }
      .checkbox-group {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .checkbox-group input {
        width: auto;
      }
      
      /* Bot list styles */
      .bot-item {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 8px;
      }
      .bot-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
      }
      .bot-name {
        font-weight: bold;
        font-size: 16px;
      }
      .bot-version {
        color: var(--blue);
        font-size: 14px;
      }
      .bot-status {
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 500;
      }
      .bot-status.validated {
        background: var(--green);
        color: white;
      }
      .bot-status.invalid {
        background: var(--red);
        color: white;
      }
      .bot-meta {
        font-size: 13px;
        color: var(--text);
        opacity: 0.8;
      }
      .bot-actions {
        display: flex;
        gap: 8px;
        margin-top: 8px;
      }
      
      /* Modal styles */
      .modal {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.7);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 1000;
      }
      .modal-content {
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 24px;
        max-width: 600px;
        width: 90%;
        max-height: 80vh;
        overflow-y: auto;
      }
      .modal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
      }
      .modal-title {
        font-size: 20px;
        font-weight: bold;
      }
      .close-btn {
        background: none;
        border: none;
        color: var(--text);
        font-size: 24px;
        cursor: pointer;
        padding: 0;
      }
      
      /* Room styles */
      .room-item {
        background: var(--panel);
        border: 1px solid var(--border);
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 12px;
      }
      .room-seats {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 8px;
        margin-top: 12px;
      }
      .seat {
        background: var(--panel-2);
        border: 1px solid var(--border);
        border-radius: 6px;
        padding: 8px;
        text-align: center;
        font-size: 13px;
      }
      .seat.occupied {
        border-color: var(--green);
      }
      .seat.ready {
        background: rgba(16, 185, 129, 0.2);
      }
      
      /* Board styles */
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
        border-radius: 16px;
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
    </style>
  </head>
  <body>
    <div class="layout">
      <aside class="sidebar">
        <div class="nav-item active" data-page="bots">🤖 My Bots</div>
        <div class="nav-item" data-page="rooms">🏠 Rooms</div>
        <div class="nav-item" data-page="games">🎮 Games</div>
        <div class="nav-item" data-page="live">📺 Live Game</div>
        <div class="nav-item" data-page="replay">🔄 Replay</div>
      </aside>

      <main>
        <!-- Bots Page -->
        <div id="botsPage" class="panel">
          <h2>🤖 My Bots</h2>
          <div class="controls">
            <button id="uploadBotBtn">Upload New Bot</button>
            <button id="refreshBotsBtn" class="secondary">Refresh</button>
          </div>
          <div id="botsList"></div>
        </div>

        <!-- Rooms Page -->
        <div id="roomsPage" class="panel hidden">
          <h2>🏠 Rooms</h2>
          <div class="controls">
            <button id="createRoomBtn">Create Room</button>
            <button id="refreshRoomsBtn" class="secondary">Refresh</button>
          </div>
          <div id="roomsList"></div>
        </div>

        <!-- Games Page -->
        <div id="gamesPage" class="panel hidden">
          <h2>🎮 Games</h2>
          <div class="controls">
            <button id="refreshGamesBtn" class="secondary">Refresh</button>
          </div>
          <div id="gamesList"></div>
        </div>

        <!-- Live Game Page -->
        <div id="livePage" class="panel hidden">
          <h2>📺 Live Game</h2>
          <div class="controls">
            <button id="createGameBtn">Create Demo Game</button>
            <button id="connectBtn" class="secondary">Connect</button>
          </div>
          <div>Game ID: <span id="gameId" class="muted">not started</span></div>
          
          <div class="status-grid">
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

          <div class="card">
            <h3>Players</h3>
            <ul id="playersList"></ul>
          </div>

          <div class="card">
            <h3>Event Feed</h3>
            <ul id="eventFeed"></ul>
          </div>

          <div class="board-wrap">
            <div id="board" class="board"></div>
          </div>
        </div>

        <!-- Replay Page -->
        <div id="replayPage" class="panel hidden">
          <h2>🔄 Replay</h2>
          <div class="controls">
            <button id="loadReplayBtn">Load Replay</button>
            <button id="stepReplayBtn" class="secondary">Step</button>
            <button id="playReplayBtn" class="ghost">Play</button>
            <button id="pauseReplayBtn" class="ghost hidden">Pause</button>
          </div>
          <div id="replaySummary" class="muted" style="margin-top: 14px;">No replay loaded.</div>
          <ul id="replayFeed" style="margin-top: 14px;"></ul>
        </div>
      </main>
    </div>

    <!-- Upload Bot Modal -->
    <div id="uploadModal" class="modal hidden">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-title">Upload New Bot</div>
          <button class="close-btn" id="closeUploadModal">&times;</button>
        </div>
        <form id="uploadBotForm">
          <div class="form-group">
            <label for="botName">Bot Name</label>
            <input type="text" id="botName" required placeholder="e.g., MyBot">
          </div>
          <div class="form-group">
            <label for="botVersion">Version</label>
            <input type="text" id="botVersion" required placeholder="e.g., v1.0.0">
          </div>
          <div class="form-group">
            <label for="botEntrypoint">Entrypoint</label>
            <input type="text" id="botEntrypoint" value="main.py">
          </div>
          <div class="form-group">
            <label for="botDescription">Description</label>
            <textarea id="botDescription" placeholder="Describe your bot's strategy..."></textarea>
          </div>
          <div class="form-group">
            <div class="checkbox-group">
              <input type="checkbox" id="useSandbox">
              <label for="useSandbox">Run in sandbox (recommended for untrusted code)</label>
            </div>
          </div>
          <div class="form-group hidden" id="botCodeGroup">
            <label for="botCode">Bot Code</label>
            <textarea id="botCode" placeholder="Paste your bot Python code here..." required></textarea>
          </div>
          <div class="controls">
            <button type="submit">Upload Bot</button>
            <button type="button" class="secondary" id="cancelUpload">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Create Room Modal -->
    <div id="roomModal" class="modal hidden">
      <div class="modal-content">
        <div class="modal-header">
          <div class="modal-title">Create Room</div>
          <button class="close-btn" id="closeRoomModal">&times;</button>
        </div>
        <form id="createRoomForm">
          <div class="form-group">
            <label for="roomName">Room Name</label>
            <input type="text" id="roomName" required placeholder="e.g., Beginner's Room">
          </div>
          <div class="form-group">
            <label for="playerName">Your Name</label>
            <input type="text" id="playerName" required placeholder="e.g., Alice">
          </div>
          <div class="controls">
            <button type="submit">Create Room</button>
            <button type="button" class="secondary" id="cancelRoom">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <script>
      // Navigation
      const navItems = document.querySelectorAll('.nav-item');
      const pages = {
        bots: document.getElementById('botsPage'),
        rooms: document.getElementById('roomsPage'),
        games: document.getElementById('gamesPage'),
        live: document.getElementById('livePage'),
        replay: document.getElementById('replayPage')
      };

      navItems.forEach(item => {
        item.addEventListener('click', () => {
          const page = item.dataset.page;
          
          // Update nav
          navItems.forEach(nav => nav.classList.remove('active'));
          item.classList.add('active');
          
          // Update pages
          Object.values(pages).forEach(p => p.classList.add('hidden'));
          pages[page].classList.remove('hidden');
          
          // Load page data
          if (page === 'bots') loadBots();
          if (page === 'rooms') loadRooms();
          if (page === 'games') loadGames();
        });
      });

      // Bot Management
      async function loadBots() {
        const response = await fetch('/bots');
        const data = await response.json();
        const botsList = document.getElementById('botsList');
        
        if (data.bots.length === 0) {
          botsList.innerHTML = '<p class="muted">No bots uploaded yet.</p>';
          return;
        }
        
        botsList.innerHTML = data.bots.map(bot => `
          <div class="bot-item">
            <div class="bot-header">
              <div>
                <span class="bot-name">${bot.name}</span>
                <span class="bot-version">${bot.version}</span>
              </div>
              <span class="bot-status ${bot.validated ? 'validated' : 'invalid'}">
                ${bot.validated ? '✓ Validated' : '✗ Invalid'}
              </span>
            </div>
            <div class="bot-meta">
              ${bot.description || 'No description'}
              ${bot.use_sandbox ? ' • 🛡️ Sandboxed' : ''}
            </div>
            ${bot.validation_errors && bot.validation_errors.length > 0 ? `
              <div style="color: var(--red); font-size: 12px; margin-top: 4px;">
                Errors: ${bot.validation_errors.join(', ')}
              </div>
            ` : ''}
            <div class="bot-actions">
              <button class="secondary" onclick="viewBot('${bot.bot_id}')">View</button>
              <button class="danger" onclick="deleteBot('${bot.bot_id}')">Delete</button>
            </div>
          </div>
        `).join('');
      }

      async function uploadBot(formData) {
        const response = await fetch('/bots/upload', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        const result = await response.json();
        
        if (result.validated) {
          alert('Bot uploaded successfully!');
          document.getElementById('uploadModal').classList.add('hidden');
          loadBots();
        } else {
          alert('Bot validation failed: ' + (result.validation_errors || []).join(', '));
        }
      }

      async function deleteBot(botId) {
        if (!confirm('Are you sure you want to delete this bot?')) return;
        
        // Note: Delete endpoint not implemented yet
        alert('Delete functionality not yet implemented');
      }

      function viewBot(botId) {
        // Note: View bot details not implemented yet
        alert('View bot details not yet implemented');
      }

      // Room Management
      async function loadRooms() {
        const response = await fetch('/rooms');
        const data = await response.json();
        const roomsList = document.getElementById('roomsList');
        
        if (!data.rooms || data.rooms.length === 0) {
          roomsList.innerHTML = '<p class="muted">No rooms available.</p>';
          return;
        }
        
        roomsList.innerHTML = data.rooms.map(room => `
          <div class="room-item">
            <div class="bot-header">
              <span class="bot-name">${room.name}</span>
              <span class="bot-status ${room.status === 'waiting' ? 'validated' : 'invalid'}">
                ${room.status}
              </span>
            </div>
            <div class="bot-meta">Created by: ${room.created_by}</div>
            <div class="room-seats">
              ${room.seats.map(seat => `
                <div class="seat ${seat.player_name ? 'occupied' : ''} ${seat.ready ? 'ready' : ''}">
                  ${seat.player_name || 'Empty'}
                  ${seat.ready ? '✓' : ''}
                </div>
              `).join('')}
            </div>
            <div class="bot-actions">
              <button onclick="joinRoom('${room.room_id}')">Join</button>
            </div>
          </div>
        `).join('');
      }

      async function createRoom(formData) {
        const response = await fetch('/rooms', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        });
        const result = await response.json();
        
        document.getElementById('roomModal').classList.add('hidden');
        loadRooms();
      }

      function joinRoom(roomId) {
        // Note: Join room functionality not fully implemented
        alert('Join room functionality not yet implemented');
      }

      // Games Management
      async function loadGames() {
        const response = await fetch('/games');
        const data = await response.json();
        const gamesList = document.getElementById('gamesList');
        
        if (!data.games || data.games.length === 0) {
          gamesList.innerHTML = '<p class="muted">No games played yet.</p>';
          return;
        }
        
        gamesList.innerHTML = data.games.map(game => `
          <div class="bot-item">
            <div class="bot-header">
              <span class="bot-name">Game: ${game.game_id}</span>
              <span class="bot-status ${game.status === 'completed' ? 'validated' : 'invalid'}">
                ${game.status}
              </span>
            </div>
            <div class="bot-meta">
              Seed: ${game.seed} • Players: ${game.players.join(', ')}
              ${game.winner ? ` • Winner: ${game.winner}` : ''}
            </div>
            <div class="bot-actions">
              <button onclick="viewGame('${game.game_id}')">View Details</button>
              <button class="secondary" onclick="viewReplay('${game.game_id}')">Replay</button>
            </div>
          </div>
        `).join('');
      }

      function viewGame(gameId) {
        // Note: View game details not implemented yet
        alert('View game details not yet implemented');
      }

      function viewReplay(gameId) {
        currentGameId = gameId;
        navItems.forEach(nav => nav.classList.remove('active'));
        document.querySelector('[data-page="replay"]').classList.add('active');
        Object.values(pages).forEach(p => p.classList.add('hidden'));
        pages.replay.classList.remove('hidden');
        loadReplay();
      }

      // Live Game
      const boardEl = document.getElementById('board');
      const eventFeedEl = document.getElementById('eventFeed');
      const playersListEl = document.getElementById('playersList');
      const gameIdEl = document.getElementById('gameId');
      const phaseEl = document.getElementById('phase');
      const turnEl = document.getElementById('turn');
      const currentPlayerEl = document.getElementById('currentPlayer');
      const winnerEl = document.getElementById('winner');
      const replaySummaryEl = document.getElementById('replaySummary');
      const replayFeedEl = document.getElementById('replayFeed');

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

      function addEvent(msg) {
        const item = document.createElement('li');
        item.textContent = `${msg.type || 'event'}${msg.data ? ' :: ' + JSON.stringify(msg.data) : ''}`;
        eventFeedEl.prepend(item);
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
        document.getElementById('playReplayBtn').classList.add('hidden');
        document.getElementById('pauseReplayBtn').classList.remove('hidden');
        replayTimer = setInterval(() => {
          if (replayIndex >= replayEvents.length) {
            clearInterval(replayTimer);
            replayTimer = null;
            document.getElementById('playReplayBtn').classList.remove('hidden');
            document.getElementById('pauseReplayBtn').classList.add('hidden');
            return;
          }
          stepReplay();
        }, 500);
      }

      function pauseReplay() {
        if (replayTimer) {
          clearInterval(replayTimer);
          replayTimer = null;
          document.getElementById('playReplayBtn').classList.remove('hidden');
          document.getElementById('pauseReplayBtn').classList.add('hidden');
        }
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

      // Modal handling
      const uploadModal = document.getElementById('uploadModal');
      const roomModal = document.getElementById('roomModal');

      document.getElementById('uploadBotBtn').addEventListener('click', () => {
        uploadModal.classList.remove('hidden');
      });

      document.getElementById('closeUploadModal').addEventListener('click', () => {
        uploadModal.classList.add('hidden');
      });

      document.getElementById('cancelUpload').addEventListener('click', () => {
        uploadModal.classList.add('hidden');
      });

      document.getElementById('useSandbox').addEventListener('change', (e) => {
        document.getElementById('botCodeGroup').classList.toggle('hidden', !e.target.checked);
      });

      document.getElementById('uploadBotForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = {
          bot_name: document.getElementById('botName').value,
          bot_version: document.getElementById('botVersion').value,
          entrypoint: document.getElementById('botEntrypoint').value,
          description: document.getElementById('botDescription').value,
          use_sandbox: document.getElementById('useSandbox').checked,
          bot_code: document.getElementById('useSandbox').checked ? document.getElementById('botCode').value : ''
        };
        uploadBot(formData);
      });

      document.getElementById('createRoomBtn').addEventListener('click', () => {
        roomModal.classList.remove('hidden');
      });

      document.getElementById('closeRoomModal').addEventListener('click', () => {
        roomModal.classList.add('hidden');
      });

      document.getElementById('cancelRoom').addEventListener('click', () => {
        roomModal.classList.add('hidden');
      });

      document.getElementById('createRoomForm').addEventListener('submit', (e) => {
        e.preventDefault();
        const formData = {
          room_name: document.getElementById('roomName').value,
          created_by: document.getElementById('playerName').value
        };
        createRoom(formData);
      });

      // Live game controls
      document.getElementById('createGameBtn').addEventListener('click', createGame);
      document.getElementById('connectBtn').addEventListener('click', () => {
        if (currentGameId) connect();
      });
      document.getElementById('loadReplayBtn').addEventListener('click', loadReplay);
      document.getElementById('stepReplayBtn').addEventListener('click', stepReplay);
      document.getElementById('playReplayBtn').addEventListener('click', playReplay);
      document.getElementById('pauseReplayBtn').addEventListener('click', pauseReplay);

      // Refresh buttons
      document.getElementById('refreshBotsBtn').addEventListener('click', loadBots);
      document.getElementById('refreshRoomsBtn').addEventListener('click', loadRooms);
      document.getElementById('refreshGamesBtn').addEventListener('click', loadGames);

      // Initialize
      renderBoard();
      renderPlayers([]);
      loadBots();
    </script>
  </body>
</html>
"""
