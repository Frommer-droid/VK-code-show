import sys

from PySide6.QtWidgets import QApplication

from .localization import install_russian_qt_translations, set_russian_qt_locale
from .resources import configure_windows_app_user_model_id, load_application_icon
from .settings import SettingsStore
from .theme import apply_global_styles
from .ui import MainWindow
from .ui_scale_runtime import resolve_ui_scale_from_screen


def main() -> int:
    configure_windows_app_user_model_id()
    set_russian_qt_locale()
    application = QApplication(sys.argv)
    install_russian_qt_translations(application)

    settings_store = SettingsStore()
    initial_scale_state = resolve_ui_scale_from_screen(
        application.primaryScreen(),
        settings_store.get_int("ui_scale_delta_percent", 0),
    )
    apply_global_styles(application, initial_scale_state.scale_factor)

    application_icon = load_application_icon()
    if not application_icon.isNull():
        application.setWindowIcon(application_icon)
    window = MainWindow(application_icon, settings_store, initial_scale_state)
    window.show_from_settings()
    QApplication.processEvents()
    window.install_ui_scale_hooks()
    return application.exec()
