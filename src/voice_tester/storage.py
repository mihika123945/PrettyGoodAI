from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TranscriptTurn:
    timestamp: str
    speaker: str
    text: str
    item_id: str | None = None


class RunStore:
    def __init__(self, data_dir: Path, run_id: str):
        self.path = data_dir / run_id
        self.path.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write_json(self, filename: str, value: Any) -> Path:
        destination = self.path / filename
        with self._lock:
            destination.write_text(
                json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8"
            )
        return destination

    def read_json(self, filename: str) -> Any:
        return json.loads((self.path / filename).read_text(encoding="utf-8"))

    def append_event(self, event: dict[str, Any]) -> None:
        with self._lock:
            with (self.path / "events.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"captured_at": utc_now(), **event}, ensure_ascii=False))
                handle.write("\n")

    def append_turn(self, turn: TranscriptTurn) -> None:
        with self._lock:
            transcript_json = self.path / "transcript.jsonl"
            with transcript_json.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(asdict(turn), ensure_ascii=False))
                handle.write("\n")
            transcript_text = self.path / "transcript.txt"
            with transcript_text.open("a", encoding="utf-8") as handle:
                label = "PATIENT BOT" if turn.speaker == "patient" else "PRACTICE AGENT"
                handle.write(f"[{turn.timestamp}] {label}: {turn.text.strip()}\n\n")

    def update_metadata(self, **updates: Any) -> None:
        filename = self.path / "metadata.json"
        with self._lock:
            current = {}
            if filename.exists():
                current = json.loads(filename.read_text(encoding="utf-8"))
            current.update(updates)
            filename.write_text(
                json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8"
            )


def find_run(data_dir: Path, run_id: str) -> RunStore:
    store = RunStore(data_dir, run_id)
    if not (store.path / "metadata.json").exists():
        raise FileNotFoundError(f"No call run found at {store.path}")
    return store
