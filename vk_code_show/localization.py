from __future__ import annotations

from pathlib import Path

import PySide6
from PySide6.QtCore import QLibraryInfo, QLocale, QTranslator
from PySide6.QtWidgets import QApplication

from .resources import resource_path


RUSSIAN_LOCALE = QLocale(QLocale.Language.Russian, QLocale.Country.Russia)


def set_russian_qt_locale() -> None:
    QLocale.setDefault(RUSSIAN_LOCALE)


def install_russian_qt_translations(application: QApplication) -> bool:
    translator = QTranslator(application)

    loaded = False
    for translations_path in _translation_directories():
        if translator.load(RUSSIAN_LOCALE, "qtbase", "_", str(translations_path)):
            loaded = True
            break

    if not loaded:
        translation_file = resource_path("PySide6/translations/qtbase_ru.qm")
        loaded = translator.load(str(translation_file))

    if not loaded:
        return False

    application.installTranslator(translator)
    translators = getattr(application, "_vk_code_show_translators", [])
    translators.append(translator)
    application._vk_code_show_translators = translators
    return True


def _translation_directories() -> list[Path]:
    pyside6_dir = Path(PySide6.__file__).resolve().parent
    return [
        Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)),
        pyside6_dir / "translations",
        resource_path("PySide6/translations"),
    ]
