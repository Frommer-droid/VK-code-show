from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from .config import DEFAULT_WINDOW_HEIGHT, DEFAULT_WINDOW_WIDTH
from .ui_scale_service import normalize_ui_scale_settings


DEFAULT_SETTINGS: dict[str, Any] = {
    "window_pos_x": None,
    "window_pos_y": None,
    "window_width": DEFAULT_WINDOW_WIDTH,
    "window_height": DEFAULT_WINDOW_HEIGHT,
    "maximized": False,
    "ui_scale_mode": "auto",
    "ui_scale_delta_percent": 0,
    "ui_scale_percent": 100,
}


def runtime_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def default_settings_path() -> Path:
    return runtime_base_dir() / "settings.json"


class SettingsStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_settings_path()
        self.data = self._load()

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def get_int(self, key: str, default: int) -> int:
        try:
            return int(self.data.get(key, default))
        except (TypeError, ValueError):
            return default

    def update(self, values: dict[str, Any], *, save: bool = True) -> None:
        self.data.update(values)
        self.data = normalize_settings(self.data)
        if save:
            self.save()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _load(self) -> dict[str, Any]:
        loaded: dict[str, Any] = {}
        if self.path.exists():
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                raw = {}
            if isinstance(raw, dict):
                loaded = raw

        return normalize_settings(loaded)


def normalize_settings(settings: dict[str, Any]) -> dict[str, Any]:
    has_delta_setting = "ui_scale_delta_percent" in settings
    has_legacy_percent = "ui_scale_percent" in settings
    normalized = {**DEFAULT_SETTINGS, **settings}
    ui_scale_source = dict(normalized)
    if has_legacy_percent and not has_delta_setting:
        ui_scale_source.pop("ui_scale_delta_percent", None)
    normalized.update(normalize_ui_scale_settings(ui_scale_source))
    normalized["window_width"] = _normalize_int(
        normalized.get("window_width"),
        DEFAULT_WINDOW_WIDTH,
        minimum=320,
    )
    normalized["window_height"] = _normalize_int(
        normalized.get("window_height"),
        DEFAULT_WINDOW_HEIGHT,
        minimum=240,
    )
    normalized["window_pos_x"] = _normalize_optional_int(normalized.get("window_pos_x"))
    normalized["window_pos_y"] = _normalize_optional_int(normalized.get("window_pos_y"))
    normalized["maximized"] = bool(normalized.get("maximized", False))
    return normalized


def _normalize_int(value: Any, default: int, *, minimum: int) -> int:
    try:
        numeric = int(value)
    except (TypeError, ValueError):
        numeric = default
    return max(minimum, numeric)


def _normalize_optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
