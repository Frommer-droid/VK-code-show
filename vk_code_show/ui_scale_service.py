from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping


BASE_LOGICAL_DPI = 96.0
REFERENCE_WIDTH = 2560
REFERENCE_HEIGHT = 1440
AUTO_SCALE_MIN_PERCENT = 70
AUTO_SCALE_MAX_PERCENT = 200
AUTO_SCALE_STEP_PERCENT = 10
DELTA_SCALE_MIN_PERCENT = -50
DELTA_SCALE_MAX_PERCENT = 50
DELTA_SCALE_STEP_PERCENT = 10
FINAL_SCALE_MIN_PERCENT = 35
FINAL_SCALE_MAX_PERCENT = 300
FINAL_SCALE_STEP_PERCENT = 5
MIN_MANUAL_SCALE_REFERENCE_PERCENT = 100
UI_SCALE_DELTA_VALUES = tuple(
    range(
        DELTA_SCALE_MIN_PERCENT,
        DELTA_SCALE_MAX_PERCENT + DELTA_SCALE_STEP_PERCENT,
        DELTA_SCALE_STEP_PERCENT,
    )
)


@dataclass(frozen=True)
class UIScaleState:
    auto_percent: int
    delta_percent: int
    final_percent: int
    scale_factor: float


def clamp_int(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def round_to_step(value: float, step: int) -> int:
    if step <= 0:
        raise ValueError("step must be positive")
    return int(math.floor((value / step) + 0.5) * step)


def normalize_ui_scale_delta_percent(value: Any) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 0
    rounded = round_to_step(numeric, DELTA_SCALE_STEP_PERCENT)
    return clamp_int(
        rounded,
        DELTA_SCALE_MIN_PERCENT,
        DELTA_SCALE_MAX_PERCENT,
    )


def normalize_ui_scale_mode(value: Any) -> str:
    return "auto"


def normalize_legacy_ui_scale_percent(value: Any) -> int:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = 100
    rounded = round_to_step(numeric, FINAL_SCALE_STEP_PERCENT)
    return clamp_int(rounded, FINAL_SCALE_MIN_PERCENT, FINAL_SCALE_MAX_PERCENT)


def calculate_auto_percent(
    available_width: int,
    available_height: int,
    logical_dpi: float,
) -> int:
    safe_width = max(1, int(available_width))
    safe_height = max(1, int(available_height))
    safe_dpi = logical_dpi if logical_dpi > 0 else BASE_LOGICAL_DPI
    normalized_width = safe_width * safe_dpi / BASE_LOGICAL_DPI
    normalized_height = safe_height * safe_dpi / BASE_LOGICAL_DPI
    ratio = min(normalized_width / REFERENCE_WIDTH, normalized_height / REFERENCE_HEIGHT)
    rounded = round_to_step(ratio * 100, AUTO_SCALE_STEP_PERCENT)
    return clamp_int(rounded, AUTO_SCALE_MIN_PERCENT, AUTO_SCALE_MAX_PERCENT)


def calculate_final_percent(auto_percent: int, delta_percent: int) -> int:
    delta_reference = max(auto_percent, MIN_MANUAL_SCALE_REFERENCE_PERCENT)
    raw_final = auto_percent + delta_reference * delta_percent / 100
    rounded = round_to_step(raw_final, FINAL_SCALE_STEP_PERCENT)
    return clamp_int(rounded, FINAL_SCALE_MIN_PERCENT, FINAL_SCALE_MAX_PERCENT)


def calculate_ui_scale_state(
    available_width: int,
    available_height: int,
    logical_dpi: float,
    delta_percent: Any,
) -> UIScaleState:
    normalized_delta = normalize_ui_scale_delta_percent(delta_percent)
    auto_percent = calculate_auto_percent(available_width, available_height, logical_dpi)
    final_percent = calculate_final_percent(auto_percent, normalized_delta)
    return UIScaleState(
        auto_percent=auto_percent,
        delta_percent=normalized_delta,
        final_percent=final_percent,
        scale_factor=final_percent / 100.0,
    )


def scale_px(value: int | float, scale_factor: float) -> int:
    numeric = float(value)
    if numeric == 0:
        return 0
    return max(1, int(round(numeric * scale_factor)))


def scale_point_size(value: int | float, scale_factor: float) -> float:
    return round(float(value) * scale_factor, 2)


def normalize_ui_scale_settings(settings: Mapping[str, Any]) -> dict[str, int | str]:
    if "ui_scale_delta_percent" in settings:
        delta_percent = normalize_ui_scale_delta_percent(settings.get("ui_scale_delta_percent"))
    else:
        legacy_percent = normalize_legacy_ui_scale_percent(settings.get("ui_scale_percent"))
        delta_percent = normalize_ui_scale_delta_percent(legacy_percent - 100)

    return {
        "ui_scale_mode": normalize_ui_scale_mode(settings.get("ui_scale_mode")),
        "ui_scale_delta_percent": delta_percent,
        "ui_scale_percent": normalize_legacy_ui_scale_percent(
            settings.get("ui_scale_percent", 100)
        ),
    }
