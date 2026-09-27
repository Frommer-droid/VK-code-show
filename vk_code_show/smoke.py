"""Noninteractive source/frozen runtime verification with isolated settings."""

from __future__ import annotations

import json
import sys
import tempfile
import traceback
from pathlib import Path


def run(report_path: Path) -> int:
    result = {"ok": False, "frozen": bool(getattr(sys, "frozen", False))}
    try:
        from PySide6.QtCore import QEvent, Qt
        from PySide6.QtGui import QKeyEvent
        from PySide6.QtGui import QFontDatabase
        from PySide6.QtWidgets import QApplication
        from . import __version__
        from .localization import install_russian_qt_translations
        from .resources import load_application_icon
        from .settings import SettingsStore
        from .theme import apply_global_styles
        from .ui import MainWindow

        app = QApplication([])
        # Windows offscreen plugin does not populate system fonts itself.
        import os

        if os.environ.get("QT_QPA_PLATFORM") == "offscreen":
            fonts = Path(os.environ["SystemRoot"]) / "Fonts"
            for name in ("tahoma.ttf", "tahomabd.ttf", "consola.ttf"):
                QFontDatabase.addApplicationFont(str(fonts / name))
        install_russian_qt_translations(app)
        apply_global_styles(app)
        icon = load_application_icon()
        assert not icon.isNull(), "Application icon is missing"
        with tempfile.TemporaryDirectory(prefix="vk-code-show-smoke-") as temp:
            window = MainWindow(icon, SettingsStore(Path(temp) / "settings.json"))
            event = QKeyEvent(
                QEvent.Type.KeyPress,
                Qt.Key.Key_V,
                Qt.KeyboardModifier.NoModifier,
                47,
                86,
                0,
                "v",
            )
            window.record_key_event(event)
            assert window.table.rowCount() == 1
            window.copy_latest_scan_code()
            assert app.clipboard().text() == "47"
            window.copy_latest_vkc_token()
            assert app.clipboard().text() == "{VKC:86}"
            window.ensurePolished()
            window.resize(1000, 700)
            app.processEvents()
            assert window.grab().save(str(report_path.with_suffix(".png")))
            window.clear_history()
            assert window.table.rowCount() == 0
            assert not window.copy_latest_scan_button.isEnabled()
            window.close()
        result.update(
            ok=True,
            version=__version__,
            checks=[
                "Qt imports",
                "translation",
                "icon",
                "window",
                "key capture",
                "scan clipboard",
                "VKC clipboard",
                "render",
                "clear history",
            ],
        )
    except Exception:
        result["error"] = traceback.format_exc()
    report_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    if sys.stdout:
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 1
