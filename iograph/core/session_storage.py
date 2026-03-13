from __future__ import annotations

from pathlib import Path
import json

from PyQt6.QtCore import QStandardPaths


class SessionStorage:
    def __init__(self, session_state_file: str, session_chunk_ms: int) -> None:
        self._session_state_file = session_state_file
        self._session_chunk_ms = int(session_chunk_ms)

    def session_state_path(self) -> Path:
        base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        if not base:
            return Path.home() / ".iograph" / self._session_state_file
        return Path(base) / self._session_state_file

    def preview_cache_path(self) -> Path:
        return self.session_state_path().with_name("preview_cache.png")

    def desktop_cache_path(self) -> Path:
        return self.session_state_path().with_name("desktop_cache.png")

    def raw_chunks_dir(self) -> Path:
        return self.session_state_path().with_name("raw_chunks")

    def save_state(self, state: dict) -> None:
        path = self.session_state_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")

    def load_state(self) -> dict | None:
        path = self.session_state_path()
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return None
        return payload if isinstance(payload, dict) else None

    def clear_state_files(self) -> None:
        path = self.session_state_path()
        if path.exists():
            try:
                path.unlink()
            except OSError:
                pass
        preview_cache = self.preview_cache_path()
        if preview_cache.exists():
            try:
                preview_cache.unlink()
            except OSError:
                pass
        desktop_cache = self.desktop_cache_path()
        if desktop_cache.exists():
            try:
                desktop_cache.unlink()
            except OSError:
                pass
        chunks_dir = self.raw_chunks_dir()
        if chunks_dir.exists() and chunks_dir.is_dir():
            for f in chunks_dir.glob("*.ndjson"):
                try:
                    f.unlink()
                except OSError:
                    pass
            try:
                chunks_dir.rmdir()
            except OSError:
                pass

    def write_raw_chunks(self, rows: list[dict]) -> dict:
        chunks_dir = self.raw_chunks_dir()
        chunks_dir.mkdir(parents=True, exist_ok=True)
        for old in chunks_dir.glob("*.ndjson"):
            try:
                old.unlink()
            except OSError:
                pass

        chunk_ms = self._session_chunk_ms
        buckets: dict[int, list[dict]] = {}
        for row in rows:
            t = int(row.get("t", 0))
            key = max(0, t // chunk_ms)
            buckets.setdefault(key, []).append(row)

        index: list[dict] = []
        for key in sorted(buckets.keys()):
            chunk_rows = buckets[key]
            fname = f"chunk_{key:06d}.ndjson"
            path = chunks_dir / fname
            with path.open("w", encoding="utf-8") as f:
                for row in chunk_rows:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")
            index.append(
                {
                    "file": fname,
                    "first_t": int(chunk_rows[0].get("t", 0)),
                    "last_t": int(chunk_rows[-1].get("t", 0)),
                    "count": len(chunk_rows),
                }
            )
        return {"format": "ndjson-chunks", "chunk_ms": chunk_ms, "chunks": index}

    def read_raw_samples(self, payload: dict) -> list[dict]:
        storage = payload.get("raw_storage")
        if isinstance(storage, dict) and storage.get("format") == "ndjson-chunks":
            chunks = storage.get("chunks", [])
            rows: list[dict] = []
            if isinstance(chunks, list):
                for chunk in chunks:
                    if not isinstance(chunk, dict):
                        continue
                    name = chunk.get("file")
                    if not isinstance(name, str):
                        continue
                    path = self.raw_chunks_dir() / name
                    if not path.exists():
                        continue
                    try:
                        for line in path.read_text(encoding="utf-8").splitlines():
                            if not line.strip():
                                continue
                            row = json.loads(line)
                            if isinstance(row, dict):
                                rows.append(row)
                    except Exception:
                        continue
            return rows

        inline = payload.get("raw_samples", [])
        if isinstance(inline, list):
            return [r for r in inline if isinstance(r, dict)]
        return []
