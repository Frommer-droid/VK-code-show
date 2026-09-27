from __future__ import annotations

from PySide6.QtGui import QScreen

from .ui_scale_service import BASE_LOGICAL_DPI, REFERENCE_HEIGHT, REFERENCE_WIDTH
from .ui_scale_service import UIScaleState, calculate_ui_scale_state


def resolve_ui_scale_from_screen(
    screen: QScreen | None,
    delta_percent: int,
) -> UIScaleState:
    if screen is None:
        return calculate_ui_scale_state(
            REFERENCE_WIDTH,
            REFERENCE_HEIGHT,
            BASE_LOGICAL_DPI,
            delta_percent,
        )

    available_geometry = screen.availableGeometry()
    return calculate_ui_scale_state(
        available_geometry.width(),
        available_geometry.height(),
        screen.logicalDotsPerInch(),
        delta_percent,
    )
