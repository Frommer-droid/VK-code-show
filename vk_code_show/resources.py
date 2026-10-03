from __future__ import annotations

import ctypes
import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon

from .config import APP_USER_MODEL_ID, ICON_FILE_NAME


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resource_path(file_name: str) -> Path:
    candidates = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(Path(meipass) / file_name)
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / file_name)
    candidates.append(project_root() / file_name)

    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[-1]


def application_icon_path() -> Path:
    return resource_path(ICON_FILE_NAME)


def load_application_icon() -> QIcon:
    return QIcon(str(application_icon_path()))


def configure_windows_app_user_model_id() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
    except Exception:
        pass
