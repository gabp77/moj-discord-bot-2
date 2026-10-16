"""Prosty storage w JSON — per-guild ustawienia (welcome channel itp.)."""
import json
from pathlib import Path
from threading import Lock

_STORAGE_FILE = Path(__file__).parent.parent / "data.json"
_LOCK = Lock()


def _load() -> dict:
    if not _STORAGE_FILE.exists():
        return {}
    try:
        return json.loads(_STORAGE_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save(data: dict) -> None:
    _STORAGE_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_guild_config(guild_id: int) -> dict:
    with _LOCK:
        data = _load()
        return data.get(str(guild_id), {})


def set_guild_value(guild_id: int, key: str, value) -> None:
    with _LOCK:
        data = _load()
        data.setdefault(str(guild_id), {})[key] = value
        _save(data)
