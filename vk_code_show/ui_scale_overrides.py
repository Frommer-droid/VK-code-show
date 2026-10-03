from __future__ import annotations

from PySide6.QtCore import QSize
from PySide6.QtWidgets import QAbstractButton, QLayout, QWidget

from .ui_scale_service import scale_px


_BASE_LAYOUT_MARGINS = "_vk_code_show_base_layout_margins"
_BASE_LAYOUT_SPACING = "_vk_code_show_base_layout_spacing"
_BASE_WIDGET_MARGINS = "_vk_code_show_base_widget_margins"
_BASE_MIN_SIZE = "_vk_code_show_base_min_size"
_BASE_MAX_SIZE = "_vk_code_show_base_max_size"
_BASE_ICON_SIZE = "_vk_code_show_base_icon_size"
_DEFAULT_MAX_SIZE = 16_000_000


def apply_scaled_metrics(root: QWidget, scale_factor: float) -> None:
    _apply_widget_metrics(root, scale_factor)
    if root.layout() is not None:
        _apply_layout_metrics(root.layout(), scale_factor)

    for widget in root.findChildren(QWidget):
        _apply_widget_metrics(widget, scale_factor)
        if widget.layout() is not None:
            _apply_layout_metrics(widget.layout(), scale_factor)


def _apply_layout_metrics(layout: QLayout, scale_factor: float) -> None:
    margins = layout.property(_BASE_LAYOUT_MARGINS)
    if margins is None:
        current = layout.contentsMargins()
        margins = (
            current.left(),
            current.top(),
            current.right(),
            current.bottom(),
        )
        layout.setProperty(_BASE_LAYOUT_MARGINS, margins)
    layout.setContentsMargins(*(scale_px(value, scale_factor) for value in margins))

    spacing = layout.property(_BASE_LAYOUT_SPACING)
    if spacing is None:
        spacing = layout.spacing()
        layout.setProperty(_BASE_LAYOUT_SPACING, spacing)
    if spacing >= 0:
        layout.setSpacing(scale_px(spacing, scale_factor))

    for index in range(layout.count()):
        item = layout.itemAt(index)
        child_layout = item.layout() if item is not None else None
        if child_layout is not None:
            _apply_layout_metrics(child_layout, scale_factor)


def _apply_widget_metrics(widget: QWidget, scale_factor: float) -> None:
    margins = widget.property(_BASE_WIDGET_MARGINS)
    if margins is None:
        current = widget.contentsMargins()
        margins = (
            current.left(),
            current.top(),
            current.right(),
            current.bottom(),
        )
        widget.setProperty(_BASE_WIDGET_MARGINS, margins)
    widget.setContentsMargins(*(scale_px(value, scale_factor) for value in margins))

    minimum_size = widget.property(_BASE_MIN_SIZE)
    if minimum_size is None:
        minimum_size = widget.minimumSize()
        widget.setProperty(_BASE_MIN_SIZE, minimum_size)
    if _is_explicit_size(minimum_size):
        widget.setMinimumSize(_scale_size(minimum_size, scale_factor))

    maximum_size = widget.property(_BASE_MAX_SIZE)
    if maximum_size is None:
        maximum_size = widget.maximumSize()
        widget.setProperty(_BASE_MAX_SIZE, maximum_size)
    if _is_explicit_max_size(maximum_size):
        widget.setMaximumSize(_scale_size(maximum_size, scale_factor))

    if isinstance(widget, QAbstractButton):
        icon_size = widget.property(_BASE_ICON_SIZE)
        if icon_size is None:
            icon_size = widget.iconSize()
            widget.setProperty(_BASE_ICON_SIZE, icon_size)
        if _is_explicit_size(icon_size):
            widget.setIconSize(_scale_size(icon_size, scale_factor))


def _is_explicit_size(size: QSize) -> bool:
    return size.width() > 0 or size.height() > 0


def _is_explicit_max_size(size: QSize) -> bool:
    return (
        (0 < size.width() < _DEFAULT_MAX_SIZE)
        or (0 < size.height() < _DEFAULT_MAX_SIZE)
    )


def _scale_size(size: QSize, scale_factor: float) -> QSize:
    width = scale_px(size.width(), scale_factor) if size.width() > 0 else 0
    height = scale_px(size.height(), scale_factor) if size.height() > 0 else 0
    return QSize(width, height)
