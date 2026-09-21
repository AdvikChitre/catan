"""Atomic on-disk job metadata and completed replay storage."""
from __future__ import annotations

import json
from pathlib import Path
import re
import threading
import uuid
import sqlite3


class ReplayStore:
    def __init__(self, directory, catalog_path=None):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.catalog_path = str(catalog_path or (self.directory / 'catalog.sqlite3'))
        with sqlite3.connect(self.catalog_path, timeout=30) as db:
            db.execute('CREATE TABLE IF NOT EXISTS match_catalog (game_id TEXT PRIMARY KEY, metadata TEXT NOT NULL)')
            # Import legacy metadata once; preserve the original replay files.
            for path in self.directory.glob('*.meta.json'):
                metadata = json.loads(path.read_text(encoding='utf-8'))
                db.execute('INSERT OR IGNORE INTO match_catalog VALUES (?, ?)',
                           (metadata['game_id'], json.dumps(metadata)))

    def _path(self, game_id, suffix):
        if not re.fullmatch(r"game-[a-zA-Z0-9-]+", game_id):
            raise KeyError(game_id)
        return self.directory / f"{game_id}.{suffix}.json"

    def _write(self, path, data):
        temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
        try:
            temporary.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def save_metadata(self, metadata):
        with self.lock, sqlite3.connect(self.catalog_path, timeout=30) as db:
            db.execute('INSERT OR REPLACE INTO match_catalog VALUES (?, ?)',
                       (metadata['game_id'], json.dumps(metadata)))

    def metadata(self, game_id):
        with sqlite3.connect(self.catalog_path, timeout=30) as db:
            row=db.execute('SELECT metadata FROM match_catalog WHERE game_id=?',(game_id,)).fetchone()
        if row is None: raise KeyError(game_id)
        return json.loads(row[0])

    def list_games(self):
        with sqlite3.connect(self.catalog_path, timeout=30) as db:
            rows=db.execute('SELECT metadata FROM match_catalog').fetchall()
        return sorted((json.loads(row[0]) for row in rows),key=lambda m:m['created_at'],reverse=True)

    def finish(self, game_id, replay, metadata):
        with self.lock:
            self._write(self._path(game_id, "replay"), replay)
            self.save_metadata(metadata)

    def save_private_audit(self, game_id, audit):
        """Never exposed by HTTP endpoints; separate from public replay files."""
        with self.lock:
            self._write(self._path(game_id, 'audit'), audit)

    def replay(self, game_id):
        self.metadata(game_id)
        path = self._path(game_id, "replay")
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None

    def recover(self):
        """Single-server deployment: jobs from an earlier process were interrupted."""
        for meta in self.list_games():
            if meta["status"] in ("queued", "running"):
                replay = self.replay(meta["game_id"])
                if replay:
                    meta.update(status=replay["result"]["status"], replay_available=True)
                else:
                    meta.update(status="failed", reason="Server stopped before this recording was saved.")
                self.save_metadata(meta)
