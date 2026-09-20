"""Atomic on-disk job metadata and completed replay storage."""
from __future__ import annotations

import json
from pathlib import Path
import re
import threading
import uuid


class ReplayStore:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()

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
        with self.lock:
            self._write(self._path(metadata["game_id"], "meta"), metadata)

    def metadata(self, game_id):
        path = self._path(game_id, "meta")
        if not path.exists():
            raise KeyError(game_id)
        return json.loads(path.read_text(encoding="utf-8"))

    def list_games(self):
        return sorted((json.loads(p.read_text(encoding="utf-8"))
                       for p in self.directory.glob("*.meta.json")),
                      key=lambda g: g["created_at"], reverse=True)

    def finish(self, game_id, replay, metadata):
        with self.lock:
            self._write(self._path(game_id, "replay"), replay)
            self.save_metadata(metadata)

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
