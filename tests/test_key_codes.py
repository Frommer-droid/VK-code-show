import unittest
from unittest.mock import patch

from vk_code_show.bootstrap import is_current_python, missing_pyside6_message, project_venv_python
from vk_code_show.key_codes import format_vk_hex, format_vkc_token, key_name_for_vk, visible_text
from vk_code_show.models import KeyCapture
from vk_code_show.resources import application_icon_path
from vk_code_show.theme import DARK_STYLE_SHEET


class KeyCodesTest(unittest.TestCase):
    def test_format_vk_hex_uses_two_digits(self) -> None:
        self.assertEqual(format_vk_hex(0x08), "0x08")
        self.assertEqual(format_vk_hex(0x41), "0x41")

    def test_format_vkc_token_uses_requested_copy_format(self) -> None:
        self.assertEqual(format_vkc_token(86), "{VKC:86}")

    def test_key_name_for_vk_prefers_known_windows_names(self) -> None:
        self.assertEqual(key_name_for_vk(0x0D), "Enter")
        self.assertEqual(key_name_for_vk(0x41), "A")

    def test_key_name_for_vk_uses_fallback_for_unknown_code(self) -> None:
        self.assertEqual(key_name_for_vk(0xE7, "Packet"), "Packet")
        self.assertEqual(key_name_for_vk(0xE7), "Unknown")

    def test_visible_text_normalizes_space_and_controls(self) -> None:
        self.assertEqual(visible_text(" "), "Space")
        self.assertEqual(visible_text("a"), "a")
        self.assertEqual(visible_text(""), "")
        self.assertEqual(visible_text("\r"), "'\\r'")

    def test_key_capture_formats_numeric_values(self) -> None:
        capture = KeyCapture(
            vk_code=0x41,
            qt_key=0x41,
            scan_code=0x001E,
            key_name="A",
            text="a",
            modifiers="",
            is_auto_repeat=False,
        )

        self.assertEqual(capture.vk_decimal, "65")
        self.assertEqual(capture.vk_hex, "0x41")
        self.assertEqual(capture.vkc_token, "{VKC:65}")
        self.assertEqual(capture.scan_decimal, "30")
        self.assertEqual(capture.scan_hex, "0x001E")
        self.assertEqual(capture.scan_display, "30 (0x001E)")
        self.assertEqual(capture.qt_hex, "0x00000041")

    def test_bootstrap_finds_project_venv(self) -> None:
        venv_python = project_venv_python()

        self.assertIsNotNone(venv_python)
        self.assertTrue(venv_python.exists())

    def test_bootstrap_detects_current_python(self) -> None:
        venv_python = project_venv_python()
        self.assertIsNotNone(venv_python)

        with patch("sys.executable", str(venv_python)):
            self.assertTrue(is_current_python(venv_python))

    def test_missing_pyside6_message_mentions_venv_run_command(self) -> None:
        self.assertIn(".\\.venv\\Scripts\\python.exe .\\VK-code-show.py", missing_pyside6_message())

    def test_application_icon_exists(self) -> None:
        icon_path = application_icon_path()

        self.assertTrue(icon_path.exists())
        self.assertEqual(icon_path.name, "logo.ico")

    def test_dark_theme_styles_core_widgets(self) -> None:
        self.assertIn("QWidget#central", DARK_STYLE_SHEET)
        self.assertIn("QTableWidget", DARK_STYLE_SHEET)
        self.assertIn("QPushButton", DARK_STYLE_SHEET)
        self.assertIn("QLabel#vkcCode", DARK_STYLE_SHEET)


if __name__ == "__main__":
    unittest.main()
