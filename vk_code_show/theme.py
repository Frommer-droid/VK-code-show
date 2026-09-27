from __future__ import annotations

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from .ui_scale_service import scale_px


THEME_COLORS = {
    "background": "#282C34",
    "surface": "#21252B",
    "surface_alt": "#2C313C",
    "surface_hover": "#353B45",
    "surface_pressed": "#181A1F",
    "alternate": "#262A32",
    "selection": "#3E4451",
    "primary": "#3E4451",
    "primary_hover": "#4B5263",
    "accent": "#61AFEF",
    "accent_hover": "#7BC0F6",
    "accent_pressed": "#4D95C7",
    "success": "#98C379",
    "text": "#ABB2BF",
    "text_strong": "#E6E6E6",
    "muted": "#9DA5B4",
    "on_accent": "#21252B",
    "border": "#3E4451",
    "focus": "#61AFEF",
    "danger": "#E06C75",
    "danger_text": "#E8838B",
    "danger_surface": "#352A31",
    "warning": "#D19A66",
    "disabled_text": "#5C6370",
    "disabled_background": "#21252B",
    "disabled_border": "#2C313C",
    "scrollbar": "#4B5263",
}


def _px(value: int, scale_factor: float) -> int:
    return scale_px(value, scale_factor)


def build_dark_stylesheet(scale_factor: float = 1.0) -> str:
    return f"""
    QWidget {{
        color: {THEME_COLORS["text_strong"]};
        font-family: Tahoma, Segoe UI, Aptos;
        font-size: {_px(13, scale_factor)}px;
    }}
    QWidget#central {{
        background: {THEME_COLORS["background"]};
    }}
    QLabel {{
        color: {THEME_COLORS["text_strong"]};
    }}
    QLabel#header {{
        color: {THEME_COLORS["text_strong"]};
        font-size: {_px(24, scale_factor)}px;
        font-weight: 700;
    }}
    QLabel#status {{
        color: {THEME_COLORS["muted"]};
    }}
    QFrame#vkCard,
    QFrame#scanCard,
    QGroupBox {{
        border: {_px(1, scale_factor)}px solid {THEME_COLORS["border"]};
        border-radius: {_px(10, scale_factor)}px;
    }}
    QFrame#vkCard {{
        background: {THEME_COLORS["surface"]};
        border-color: {THEME_COLORS["border"]};
    }}
    QFrame#scanCard {{
        background: {THEME_COLORS["surface_alt"]};
        border-color: {THEME_COLORS["border"]};
    }}
    QGroupBox {{
        margin-top: {_px(12, scale_factor)}px;
        padding-top: {_px(12, scale_factor)}px;
        font-weight: 600;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        left: {_px(10, scale_factor)}px;
        padding: 0 {_px(4, scale_factor)}px;
        color: {THEME_COLORS["text"]};
    }}
    QLabel[role="caption"] {{
        color: {THEME_COLORS["muted"]};
        font-size: {_px(12, scale_factor)}px;
    }}
    QLabel#vkCardTitle,
    QLabel#scanCardTitle {{
        font-size: {_px(12, scale_factor)}px;
        font-weight: 700;
        letter-spacing: {_px(1, scale_factor)}px;
    }}
    QLabel#vkCardTitle {{
        color: {THEME_COLORS["accent"]};
    }}
    QLabel#scanCardTitle {{
        color: {THEME_COLORS["success"]};
    }}
    QLabel#vkValue,
    QLabel#scanValue {{
        font-family: Consolas, Cascadia Mono, monospace;
        font-size: {_px(36, scale_factor)}px;
        font-weight: 700;
    }}
    QLabel#vkValue {{
        color: {THEME_COLORS["accent"]};
    }}
    QLabel#scanValue {{
        color: {THEME_COLORS["success"]};
    }}
    QLabel#scanDescription {{
        color: {THEME_COLORS["muted"]};
    }}
    QLabel#vkcCode {{
        background: {THEME_COLORS["surface"]};
        border: {_px(1, scale_factor)}px solid {THEME_COLORS["selection"]};
        border-radius: {_px(6, scale_factor)}px;
        color: {THEME_COLORS["accent"]};
        font-family: Consolas, Cascadia Mono, monospace;
        font-size: {_px(22, scale_factor)}px;
        font-weight: 700;
        padding: {_px(8, scale_factor)}px {_px(10, scale_factor)}px;
    }}
    QPushButton,
    QComboBox {{
        background: {THEME_COLORS["surface_hover"]};
        border: {_px(1, scale_factor)}px solid {THEME_COLORS["border"]};
        border-radius: {_px(6, scale_factor)}px;
        color: {THEME_COLORS["text_strong"]};
        min-height: {_px(28, scale_factor)}px;
        padding: {_px(7, scale_factor)}px {_px(12, scale_factor)}px;
    }}
    QPushButton:hover,
    QComboBox:hover {{
        background: {THEME_COLORS["primary_hover"]};
        border-color: {THEME_COLORS["accent"]};
    }}
    QPushButton:pressed {{
        background: {THEME_COLORS["surface_pressed"]};
        border-color: {THEME_COLORS["accent_pressed"]};
        color: {THEME_COLORS["text_strong"]};
    }}
    QPushButton:disabled {{
        background: {THEME_COLORS["disabled_background"]};
        border-color: {THEME_COLORS["disabled_border"]};
        color: {THEME_COLORS["disabled_text"]};
    }}
    QPushButton#copyVkcButton {{
        font-weight: 600;
        min-width: {_px(118, scale_factor)}px;
    }}
    QPushButton#copyScanButton {{
        background: {THEME_COLORS["primary"]};
        border-color: {THEME_COLORS["border"]};
        color: {THEME_COLORS["text_strong"]};
        font-weight: 700;
    }}
    QPushButton#copyScanButton:hover {{
        background: {THEME_COLORS["primary_hover"]};
        border-color: {THEME_COLORS["success"]};
    }}
    QPushButton#copyScanButton:pressed {{
        background: {THEME_COLORS["surface_pressed"]};
        border-color: {THEME_COLORS["focus"]};
    }}
    QPushButton#copyScanButton:disabled {{
        background: {THEME_COLORS["disabled_background"]};
        border-color: {THEME_COLORS["disabled_border"]};
        color: {THEME_COLORS["disabled_text"]};
    }}
    QPushButton:focus, QComboBox:focus {{
        border-color: {THEME_COLORS["focus"]};
    }}
    QPushButton:checked, QComboBox:on {{
        background: {THEME_COLORS["selection"]};
    }}
    QComboBox:disabled {{
        background: {THEME_COLORS["disabled_background"]};
        color: {THEME_COLORS["disabled_text"]};
        border-color: {THEME_COLORS["disabled_border"]};
    }}
    QScrollBar::handle:hover {{ background: {THEME_COLORS["primary_hover"]}; }}
    QScrollBar::handle:pressed {{ background: {THEME_COLORS["accent"]}; }}
    QComboBox::drop-down {{
        border: 0;
        width: {_px(24, scale_factor)}px;
    }}
    QComboBox QAbstractItemView {{
        background: {THEME_COLORS["surface"]};
        border: {_px(1, scale_factor)}px solid {THEME_COLORS["border"]};
        selection-background-color: {THEME_COLORS["selection"]};
        selection-color: {THEME_COLORS["text_strong"]};
    }}
    QTableWidget {{
        alternate-background-color: {THEME_COLORS["alternate"]};
        font-size: {_px(15, scale_factor)}px;
        background: {THEME_COLORS["surface"]};
        border: {_px(1, scale_factor)}px solid {THEME_COLORS["border"]};
        border-radius: {_px(6, scale_factor)}px;
        color: {THEME_COLORS["text_strong"]};
        gridline-color: {THEME_COLORS["border"]};
        selection-background-color: {THEME_COLORS["selection"]};
        selection-color: {THEME_COLORS["text_strong"]};
    }}
    QTableWidget::item {{
        padding: {_px(4, scale_factor)}px;
    }}
    QTableWidget::item:selected {{
        background: {THEME_COLORS["selection"]};
        color: {THEME_COLORS["text_strong"]};
    }}
    QHeaderView::section {{
        background: {THEME_COLORS["surface_alt"]};
        font-size: {_px(14, scale_factor)}px;
        border: 0;
        border-right: {_px(1, scale_factor)}px solid {THEME_COLORS["border"]};
        color: {THEME_COLORS["text"]};
        font-weight: 600;
        padding: {_px(6, scale_factor)}px;
    }}
    QTableCornerButton::section {{
        background: {THEME_COLORS["surface_alt"]};
        border: 0;
    }}
    QScrollBar:vertical {{
        background: {THEME_COLORS["surface"]};
        width: {_px(12, scale_factor)}px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {THEME_COLORS["border"]};
        border-radius: {_px(5, scale_factor)}px;
        min-height: {_px(28, scale_factor)}px;
    }}
    QScrollBar:horizontal {{
        background: {THEME_COLORS["surface"]};
        height: {_px(12, scale_factor)}px;
        margin: 0;
    }}
    QScrollBar::handle:horizontal {{
        background: {THEME_COLORS["border"]};
        border-radius: {_px(5, scale_factor)}px;
        min-width: {_px(28, scale_factor)}px;
    }}
    QToolTip {{
        background: {THEME_COLORS["surface_hover"]};
        border: {_px(1, scale_factor)}px solid {THEME_COLORS["border"]};
        color: {THEME_COLORS["text_strong"]};
        padding: {_px(4, scale_factor)}px;
    }}
"""


def apply_global_styles(application: QApplication, scale_factor: float = 1.0) -> None:
    application.setStyle("Fusion")
    palette = QPalette()
    for role, token in {
        QPalette.ColorRole.Window: "background",
        QPalette.ColorRole.WindowText: "text_strong",
        QPalette.ColorRole.Base: "surface",
        QPalette.ColorRole.AlternateBase: "alternate",
        QPalette.ColorRole.Text: "text_strong",
        QPalette.ColorRole.Button: "surface_hover",
        QPalette.ColorRole.ButtonText: "text_strong",
        QPalette.ColorRole.Highlight: "selection",
        QPalette.ColorRole.HighlightedText: "text_strong",
    }.items():
        palette.setColor(role, QColor(THEME_COLORS[token]))
    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.ButtonText,
        QPalette.ColorRole.WindowText,
    ):
        palette.setColor(
            QPalette.ColorGroup.Disabled, role, QColor(THEME_COLORS["disabled_text"])
        )
    application.setPalette(palette)
    application.setStyleSheet(build_dark_stylesheet(scale_factor))


DARK_STYLE_SHEET = build_dark_stylesheet()
