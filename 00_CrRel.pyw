# -*- coding: utf-8 -*-
"""
Build the VK-code-show Inno Setup installer from the prepared portable folder.

Expected input:
  <project root>\\VK-code-show

Generated setup:
  <Windows Desktop>\\VK-code-show_v<VERSION>_Setup.exe
"""

from __future__ import annotations

import ast
import ctypes
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import tkinter as tk
from pathlib import Path


APP_NAME = "VK-code-show"
APP_DISPLAY_NAME = "VK Code Show"
APP_PUBLISHER = "Frommer-droid"
APP_ID = "9F2B7983-1EB5-4F38-A3BC-77A84377D86A"
EXE_NAME = f"{APP_NAME}.exe"

SCRIPT_DIR = Path(__file__).resolve().parent
SOURCE_DIR = SCRIPT_DIR / APP_NAME
WORK_DIR = SCRIPT_DIR / "_release_work" / "installer"
def desktop_dir() -> Path:
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
            value, _ = winreg.QueryValueEx(key, "Desktop")
        return Path(os.path.expandvars(value))
    except OSError:
        import uuid
        guid = (ctypes.c_ubyte * 16).from_buffer_copy(
            uuid.UUID("B4BFCC3A-DB2C-424C-B029-7FE99A87C641").bytes_le)
        pointer = ctypes.c_wchar_p()
        if ctypes.windll.shell32.SHGetKnownFolderPath(
                ctypes.byref(guid), 0, None, ctypes.byref(pointer)) == 0:
            try:
                return Path(pointer.value)
            finally:
                ctypes.windll.ole32.CoTaskMemFree(ctypes.cast(pointer, ctypes.c_void_p))
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buffer) == 0:
            return Path(buffer.value)
        return Path.home() / "Desktop"


DESKTOP_DIR = desktop_dir()
PACKAGE_INIT = SCRIPT_DIR / "vk_code_show" / "__init__.py"
VERSION_FILE = SCRIPT_DIR / "VERSION"

REQUIRED_RELEASE_FILES = (
    EXE_NAME,
    "logo.ico",
    "VERSION",
    "RUNTIME_MANIFEST.json",
    "LICENSE",
    "THIRD_PARTY_NOTICES.md",
)
REQUIRED_RELEASE_DIRS = (
    "_internal",
)
RUNTIME_NOISE_FILES = (
    ".env",
    "settings.json",
    "app.log",
    "vk-code-show.log",
    "launch_cache.json",
)

ISCC_CANDIDATE_PATHS = (
    os.environ.get("INNO_SETUP_ISCC", ""),
    r"D:\dev\tools\Inno Setup 6\ISCC.exe",
    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    r"C:\Program Files\Inno Setup 6\ISCC.exe",
    shutil.which("ISCC.exe") or "",
)


def _configure_stdout() -> None:
    if sys.stdout:
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def log(message: str) -> None:
    if not sys.stdout:
        return
    try:
        print(message)
    except Exception:
        pass


def find_iscc_path() -> str:
    for path in ISCC_CANDIDATE_PATHS:
        if path and os.path.isfile(path):
            return path
    return ""


def remove_readonly(func, path, _exc_info) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as exc:
        log(f"Could not remove {path}: {exc}")


def show_popup(message: str, is_error: bool = False) -> None:
    try:
        root = tk.Tk()
        root.attributes("-topmost", True)

        if is_error:
            root.title("Error")
            bg_color = "#ffcccc"
        else:
            root.overrideredirect(True)
            bg_color = "#e6ffe6"

        root.configure(bg=bg_color)
        width = 620 if is_error else 500
        height = 240 if is_error else 150
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f"{width}x{height}+{x}+{y}")

        label = tk.Label(
            root,
            text=message,
            font=("Arial", 11),
            bg=bg_color,
            wraplength=width - 30,
        )
        label.pack(expand=True, padx=20, pady=18)

        if is_error:
            button = tk.Button(root, text="Close", command=root.destroy)
            button.pack(pady=(0, 14))
        else:
            root.after(3500, root.destroy)
            root.bind("<Button-1>", lambda _event: root.destroy())
            label.bind("<Button-1>", lambda _event: root.destroy())

        root.mainloop()
    except Exception:
        log(message)


def kill_process_smart(process_name: str, path_filter: Path | None = None) -> None:
    log(f"--- Checking process: {process_name} ---")
    process_name_no_ext = process_name.removesuffix(".exe")

    for _attempt in range(3):
        if path_filter:
            escaped_path = str(path_filter).replace("'", "''")
            escaped_name = process_name_no_ext.replace("'", "''")
            ps_command = (
                f"$name = '{escaped_name}'; "
                f"$target = [System.IO.Path]::GetFullPath('{escaped_path}'); "
                "if (-not $target.EndsWith([System.IO.Path]::DirectorySeparatorChar)) "
                "{ $target += [System.IO.Path]::DirectorySeparatorChar }; "
                "Get-Process -Name $name -ErrorAction SilentlyContinue | "
                "Where-Object { $_.Path -and "
                "([System.IO.Path]::GetFullPath($_.Path)).StartsWith($target, "
                "[System.StringComparison]::OrdinalIgnoreCase) } | "
                "Stop-Process -Force"
            )
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    ps_command,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        else:
            subprocess.run(
                ["taskkill", "/F", "/IM", process_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        time.sleep(0.5)


def should_remove_root_file(filename: str) -> bool:
    name_lower = filename.lower()
    return (
        name_lower.endswith(".log")
        or ".log." in name_lower
        or name_lower in RUNTIME_NOISE_FILES
    )


def get_missing_release_items(source_dir: Path) -> dict[str, list[str]]:
    missing_files = [
        filename
        for filename in REQUIRED_RELEASE_FILES
        if not (source_dir / filename).is_file()
    ]
    missing_dirs = [
        dirname
        for dirname in REQUIRED_RELEASE_DIRS
        if not (source_dir / dirname).is_dir()
    ]
    return {"files": missing_files, "directories": missing_dirs}


def format_missing_release_items(missing: dict[str, list[str]]) -> str:
    lines = []
    if missing["files"]:
        lines.append("Missing files:")
        lines.extend(f"- {name}" for name in missing["files"])
    if missing["directories"]:
        lines.append("Missing directories:")
        lines.extend(f"- {name}" for name in missing["directories"])
    return "\n".join(lines)


def prepare_release_folder(source: Path, destination: Path) -> bool:
    log(f"--- Preparing installer staging from {source} ---")

    if destination.exists():
        try:
            shutil.rmtree(destination, onerror=remove_readonly)
        except Exception:
            pass

    try:
        shutil.copytree(source, destination)
    except Exception as exc:
        log(f"Copy failed: {exc}")
        return False

    keep_folders_lower = tuple(folder.lower() for folder in REQUIRED_RELEASE_DIRS)

    for item in destination.iterdir():
        if item.is_dir():
            if item.name.lower() not in keep_folders_lower:
                try:
                    shutil.rmtree(item, onerror=remove_readonly)
                    log(f"Removed folder: {item.name}")
                except Exception:
                    subprocess.run(
                        ["cmd", "/c", "rmdir", "/s", "/q", str(item)],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
            else:
                log(f"Kept folder: {item.name}")
            continue

        if should_remove_root_file(item.name):
            try:
                item.unlink()
                log(f"Removed runtime file: {item.name}")
            except Exception as exc:
                log(f"Could not remove {item.name}: {exc}")
        else:
            log(f"Kept file: {item.name}")

    return True


def _read_package_version() -> str:
    if not PACKAGE_INIT.exists():
        return ""

    try:
        tree = ast.parse(PACKAGE_INIT.read_text(encoding="utf-8"))
    except Exception:
        return ""

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except Exception:
            return ""
        return str(value).strip()

    return ""


def read_version() -> str:
    if VERSION_FILE.exists():
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
        if version:
            return version

    return _read_package_version() or "0.1.0"


def normalize_version_info(version: str) -> str:
    parts: list[str] = []
    for chunk in version.split("."):
        match = re.match(r"\d+", chunk)
        if not match:
            break
        parts.append(match.group(0))

    while len(parts) < 4:
        parts.append("0")

    return ".".join(parts[:4])


def _is_fixed_drive(root: Path) -> bool:
    if os.name != "nt":
        return False
    try:
        return ctypes.windll.kernel32.GetDriveTypeW(str(root)) == 3
    except Exception:
        return False


def choose_default_install_dir() -> Path:
    d_drive = Path("D:/")
    if _is_fixed_drive(d_drive):
        return d_drive / "Apps" / APP_NAME

    for codepoint in range(ord("E"), ord("Z") + 1):
        drive = Path(f"{chr(codepoint)}:/")
        if _is_fixed_drive(drive):
            return drive / "Apps" / APP_NAME

    return Path("C:/Apps") / APP_NAME


def _escape_iss_path(path: Path) -> str:
    return str(path).rstrip("\\")


def build_iss_content(version: str, icon_line: str) -> str:
    template = r"""; Inno Setup script for VK-code-show.
; Generated by 00_CrRel.pyw.

#define MyAppName "__APP_NAME__"
#define MyAppDisplayName "__APP_DISPLAY_NAME__"
#define MyAppVersion "__VERSION__"
#define MyAppPublisher "__APP_PUBLISHER__"
#define MyAppExeName "__EXE_NAME__"

[Setup]
AppId={{__APP_ID__}
AppName={#MyAppDisplayName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName=__DEFAULT_INSTALL_DIR__
UsePreviousAppDir=no
DefaultGroupName={#MyAppDisplayName}
DisableProgramGroupPage=yes
OutputDir=__OUTPUT_DIR__
OutputBaseFilename={#MyAppName}_v{#MyAppVersion}_Setup
__ICON_LINE__
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
VersionInfoVersion=__VERSION_INFO__
VersionInfoTextVersion={#MyAppVersion}
VersionInfoProductVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppDisplayName} Setup
VersionInfoProductName={#MyAppDisplayName}
UninstallDisplayIcon={app}\logo.ico

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: checkedonce

[Files]
Source: "__WORK_DIR__\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"
Name: "{group}\Uninstall {#MyAppDisplayName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppDisplayName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\logo.ico"; Tasks: desktopicon

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillApp"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Запустить {#MyAppDisplayName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
"""

    return (
        template.replace("__APP_NAME__", APP_NAME)
        .replace("__APP_DISPLAY_NAME__", APP_DISPLAY_NAME)
        .replace("__VERSION__", version)
        .replace("__VERSION_INFO__", normalize_version_info(version))
        .replace("__APP_PUBLISHER__", APP_PUBLISHER)
        .replace("__EXE_NAME__", EXE_NAME)
        .replace("__APP_ID__", APP_ID)
        .replace("__OUTPUT_DIR__", _escape_iss_path(DESKTOP_DIR))
        .replace("__DEFAULT_INSTALL_DIR__", _escape_iss_path(choose_default_install_dir()))
        .replace("__ICON_LINE__", icon_line)
        .replace("__WORK_DIR__", _escape_iss_path(WORK_DIR))
    )


def main() -> None:
    _configure_stdout()
    log("--- Creating VK-code-show setup installer ---")

    iscc_path = find_iscc_path()
    if not iscc_path:
        show_popup(
            "Inno Setup compiler was not found.\n"
            "Install Inno Setup 6 or set INNO_SETUP_ISCC to ISCC.exe.",
            is_error=True,
        )
        return

    if not SOURCE_DIR.is_dir():
        show_popup(
            "Portable folder was not found:\n"
            f"{SOURCE_DIR}\n\n"
            "Build the application first with Build_Tools/SpecCompiler.pyw.",
            is_error=True,
        )
        return

    missing = get_missing_release_items(SOURCE_DIR)
    if missing["files"] or missing["directories"]:
        show_popup(
            "Portable folder is incomplete.\n\n"
            f"{format_missing_release_items(missing)}",
            is_error=True,
        )
        return

    version = read_version()
    if (SOURCE_DIR / "VERSION").read_text(encoding="utf-8").strip() != version:
        raise RuntimeError("Portable VERSION does not match the requested installer version")

    kill_process_smart(EXE_NAME, path_filter=SOURCE_DIR)

    if not prepare_release_folder(SOURCE_DIR, WORK_DIR):
        show_popup("Failed to prepare installer staging folder.", is_error=True)
        return

    icon_path = WORK_DIR / "logo.ico"
    icon_line = f"SetupIconFile={_escape_iss_path(icon_path)}" if icon_path.exists() else ""
    iss_content = build_iss_content(version, icon_line)

    iss_path = Path(tempfile.gettempdir()) / "vk_code_show_installer.iss"
    iss_path.write_text(iss_content, encoding="utf-8")

    DESKTOP_DIR.mkdir(parents=True, exist_ok=True)
    command = [iscc_path, str(iss_path)]
    log("Command: " + " ".join(command))

    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as exc:
        show_popup(
            "Inno Setup failed.\n\n"
            f"{exc.stderr or exc.stdout or exc}",
            is_error=True,
        )
        return
    finally:
        try:
            iss_path.unlink()
        except OSError:
            pass
        try:
            shutil.rmtree(WORK_DIR, onerror=remove_readonly)
        except OSError:
            pass

    if result.stdout:
        log(result.stdout)

    setup_name = f"{APP_NAME}_v{version}_Setup.exe"
    show_popup(f"Setup is ready:\n{DESKTOP_DIR / setup_name}")


if __name__ == "__main__":
    main()
