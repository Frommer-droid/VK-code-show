import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QGroupBox

from vk_code_show.settings import SettingsStore
from vk_code_show.theme import build_dark_stylesheet
from vk_code_show.ui import MainWindow
from vk_code_show.ui_scale_service import (
    UIScaleState,
    calculate_auto_percent,
    calculate_final_percent,
    calculate_ui_scale_state,
    normalize_ui_scale_settings,
    scale_px,
)


class UIScaleFormulaTest(unittest.TestCase):
    def test_reference_screen_resolves_to_100_percent(self) -> None:
        state = calculate_ui_scale_state(2560, 1440, 96.0, 0)

        self.assertEqual(state, UIScaleState(100, 0, 100, 1.0))

    def test_auto_scale_uses_available_size_and_dpi(self) -> None:
        self.assertEqual(calculate_auto_percent(1920, 1080, 96.0), 80)
        self.assertEqual(calculate_auto_percent(1920, 1080, 144.0), 110)

    def test_final_scale_uses_delta_reference_and_clamps(self) -> None:
        self.assertEqual(calculate_final_percent(80, 20), 100)
        self.assertEqual(calculate_final_percent(70, -50), 35)
        self.assertEqual(calculate_final_percent(200, 50), 300)

    def test_legacy_percent_migrates_to_delta(self) -> None:
        normalized = normalize_ui_scale_settings({"ui_scale_percent": 130})

        self.assertEqual(normalized["ui_scale_mode"], "auto")
        self.assertEqual(normalized["ui_scale_delta_percent"], 30)

    def test_scale_px_preserves_zero_and_scales_positive_values(self) -> None:
        self.assertEqual(scale_px(0, 1.5), 0)
        self.assertEqual(scale_px(10, 1.5), 15)


class SettingsStoreTest(unittest.TestCase):
    def test_settings_store_loads_defaults_and_saves_normalized_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            store = SettingsStore(settings_path)

            self.assertEqual(store.get("ui_scale_mode"), "auto")
            self.assertEqual(store.get("ui_scale_delta_percent"), 0)

            store.update({"ui_scale_delta_percent": 27}, save=True)
            reloaded = SettingsStore(settings_path)

        self.assertEqual(reloaded.get("ui_scale_delta_percent"), 30)

    def test_settings_store_recovers_from_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings_path.write_text("{", encoding="utf-8")

            store = SettingsStore(settings_path)

        self.assertEqual(store.get("window_width"), 760)
        self.assertEqual(store.get("ui_scale_percent"), 100)

    def test_settings_store_migrates_legacy_percent_to_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_path = Path(temp_dir) / "settings.json"
            settings_path.write_text('{"ui_scale_percent": 130}', encoding="utf-8")

            store = SettingsStore(settings_path)

        self.assertEqual(store.get("ui_scale_delta_percent"), 30)


class ThemeScaleTest(unittest.TestCase):
    def test_stylesheet_metrics_follow_scale_factor(self) -> None:
        stylesheet = build_dark_stylesheet(2.0)

        self.assertIn("font-size: 26px", stylesheet)
        self.assertIn("min-width: 236px", stylesheet)


class MainWindowUIScaleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.application = QApplication.instance() or QApplication([])

    def tearDown(self) -> None:
        self.application.processEvents()

    def _dispose_window(self, window: MainWindow) -> None:
        window.close()
        window.deleteLater()
        self.application.processEvents()

    def test_window_contains_russian_scale_group_and_delta_combo(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SettingsStore(Path(temp_dir) / "settings.json")
            window = MainWindow(
                settings_store=store,
                initial_scale_state=UIScaleState(100, 0, 100, 1.0),
            )
            try:
                group = window.findChild(QGroupBox)

                self.assertIsNotNone(group)
                self.assertEqual(group.title(), "Масштаб интерфейса")
                self.assertEqual(window.ui_scale_combo.count(), 11)
                self.assertEqual(window.ui_scale_combo.itemText(0), "50%")
                self.assertEqual(window.ui_scale_combo.itemData(0), -50)
                self.assertEqual(window.ui_scale_combo.itemText(10), "150%")
                self.assertEqual(window.ui_scale_combo.itemData(10), 50)
            finally:
                self._dispose_window(window)

    def test_manual_scale_change_is_saved_as_delta(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SettingsStore(Path(temp_dir) / "settings.json")
            window = MainWindow(
                settings_store=store,
                initial_scale_state=UIScaleState(100, 0, 100, 1.0),
            )
            try:
                window.ui_scale_combo.setCurrentIndex(window.ui_scale_combo.findData(20))

                self.assertEqual(store.get("ui_scale_delta_percent"), 20)
                self.assertEqual(window.ui_scale_combo.currentData(), 20)
            finally:
                self._dispose_window(window)

    def test_window_minimum_size_uses_single_scale_pass(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            store = SettingsStore(Path(temp_dir) / "settings.json")
            window = MainWindow(
                settings_store=store,
                initial_scale_state=UIScaleState(100, 0, 100, 1.0),
            )
            try:
                self.assertEqual(window.minimumWidth(), 620)
                self.assertEqual(window.minimumHeight(), 420)
            finally:
                self._dispose_window(window)


if __name__ == "__main__":
    unittest.main()
