# -*- mode: python ; coding: utf-8 -*-

import os
import sys
from pathlib import Path

import PySide6


block_cipher = None

SPEC_DIR = Path(SPECPATH).resolve()
PROJECT_ROOT = SPEC_DIR.parent
sys.path.insert(0, str(SPEC_DIR))
from runtime_dll_policy import minimal_path, qt_runtime
from PyInstaller.utils.win32.versioninfo import (
    VSVersionInfo, FixedFileInfo, StringFileInfo, StringTable, StringStruct,
    VarFileInfo, VarStruct,
)

os.environ["PATH"] = minimal_path()
APP_NAME = "VK-code-show"
ENTRY_SCRIPT = PROJECT_ROOT / "VK-code-show.py"
ICON_FILE = PROJECT_ROOT / "logo.ico"
VERSION_FILE = PROJECT_ROOT / "VERSION"
PYSIDE6_DIR = Path(PySide6.__file__).resolve().parent
QTBASE_RU_TRANSLATION = PYSIDE6_DIR / "translations" / "qtbase_ru.qm"

datas = []
datas.append((str(PROJECT_ROOT / "assets/licenses"), "licenses/Qt"))
datas.append((str(Path(sys.base_prefix) / "LICENSE.txt"), "licenses/Python"))
for name in ("LICENSE", "THIRD_PARTY_NOTICES.md", "RELEASE_NOTES.md"):
    datas.append((str(PROJECT_ROOT / name), "."))
if ICON_FILE.exists():
    datas.append((str(ICON_FILE), "."))
if VERSION_FILE.exists():
    datas.append((str(VERSION_FILE), "."))
if QTBASE_RU_TRANSLATION.exists():
    datas.append((str(QTBASE_RU_TRANSLATION), "PySide6/translations"))

a = Analysis(
    [str(ENTRY_SCRIPT)],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=[
        "PySide6.QtCore",
        "PySide6.QtGui",
        "PySide6.QtWidgets",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["PIL", "tkinter", "pytest", "ruff"],
    noarchive=False,
)

a.binaries = qt_runtime(a.binaries, PROJECT_ROOT)
version_text = VERSION_FILE.read_text(encoding="utf-8").strip()
version_tuple = tuple(int(part) for part in version_text.split(".")) + (0,)
version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=version_tuple, prodvers=version_tuple,
                     mask=0x3f, flags=0, OS=0x40004, fileType=1, subtype=0, date=(0, 0)),
    kids=[StringFileInfo([StringTable("040904B0", [
        StringStruct("FileDescription", "VK Code Show"),
        StringStruct("ProductName", "VK Code Show"),
        StringStruct("FileVersion", version_text),
        StringStruct("ProductVersion", version_text),
        StringStruct("OriginalFilename", APP_NAME + ".exe"),
        StringStruct("CompanyName", "Frommer-droid"),
    ])]), VarFileInfo([VarStruct("Translation", [1033, 1200])])],
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    version=version_info,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(ICON_FILE) if ICON_FILE.exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
