# -*- coding: utf-8 -*-
"""
Update the portable VK-code-show folder.

The script copies the already prepared <project root>\\VK-code-show folder to
D:\\Portable_soft\\VK-code-show. Resource preparation is handled by Build_Tools.
"""

from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
import time
import tkinter as tk


APP_NAME = "VK-code-show"
EXE_NAME = f"{APP_NAME}.exe"
DESTINATION_PARENT = r"D:\Portable_soft"
SKIP_AUTORUN_ENV = "VK_CODE_SHOW_SKIP_AUTORUN"

REQUIRED_SOURCE_ITEMS = (
    EXE_NAME,
    "_internal",
    "logo.ico",
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


def remove_readonly(func, path, _exc_info) -> None:
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception as exc:
        log(f"Could not remove {path}: {exc}")


def show_popup(message: str = "Done", is_error: bool = False) -> None:
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
        width = 580 if is_error else 450
        height = 220 if is_error else 130
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


def kill_process_smart(process_name: str, path_filter: str | None = None) -> None:
    log(f"--- Checking process: {process_name} ---")
    process_name_no_ext = process_name.removesuffix(".exe")

    for _attempt in range(3):
        if path_filter:
            escaped_path = path_filter.replace("'", "''")
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


def _resolve_path(path: str) -> str:
    return os.path.normcase(os.path.abspath(path))


def ensure_target_is_safe(target_path: str) -> None:
    parent = _resolve_path(DESTINATION_PARENT)
    target = _resolve_path(target_path)
    parent_with_sep = parent if parent.endswith(os.sep) else parent + os.sep

    if target == parent or not target.startswith(parent_with_sep):
        raise ValueError(f"Unsafe target path: {target_path}")


def validate_source_folder(source_folder: str) -> list[str]:
    missing: list[str] = []
    for item in REQUIRED_SOURCE_ITEMS:
        item_path = os.path.join(source_folder, item)
        if not os.path.exists(item_path):
            missing.append(item)
    return missing


def remove_existing_folder(target_folder: str) -> bool:
    if not os.path.exists(target_folder):
        log(f"Target folder does not exist, skipping removal: {target_folder}")
        return True

    log(f"Removing old target folder: {target_folder}")
    for attempt in range(1, 4):
        try:
            shutil.rmtree(target_folder, onerror=remove_readonly)
        except OSError as exc:
            log(f"Removal attempt {attempt}/3 failed: {exc}")
        if not os.path.exists(target_folder):
            return True
        log(f"Removal attempt {attempt}/3 left target in place.")
        time.sleep(1)

    return not os.path.exists(target_folder)


def copy_release_folder(source_folder: str, target_folder: str) -> None:
    shutil.copytree(
        source_folder,
        target_folder,
        dirs_exist_ok=os.path.exists(target_folder),
    )


def manage_folders() -> None:
    _configure_stdout()

    base_dir = os.path.abspath(os.path.dirname(__file__))
    source_folder = os.path.join(base_dir, APP_NAME)
    target_folder = os.path.join(DESTINATION_PARENT, APP_NAME)

    log(f"Source: {source_folder}")
    log(f"Target: {target_folder}")

    if os.environ.get(SKIP_AUTORUN_ENV, "").strip() == "1":
        log(f"[INFO] {SKIP_AUTORUN_ENV}=1; no post-copy autorun will be performed.")

    if not os.path.isdir(source_folder):
        show_popup(
            "Portable source folder was not found:\n"
            f"{source_folder}\n\n"
            "Build the application first with Build_Tools/SpecCompiler.pyw.",
            is_error=True,
        )
        return

    missing = validate_source_folder(source_folder)
    if missing:
        show_popup(
            "Portable source folder is incomplete:\n"
            + "\n".join(f"- {name}" for name in missing),
            is_error=True,
        )
        return

    try:
        ensure_target_is_safe(target_folder)
    except ValueError as exc:
        show_popup(str(exc), is_error=True)
        return

    os.makedirs(DESTINATION_PARENT, exist_ok=True)

    kill_process_smart(EXE_NAME, path_filter=target_folder)
    time.sleep(1)

    if not remove_existing_folder(target_folder):
        log(
            "[WARN] Could not fully remove the old portable folder. "
            "Copying the prepared build over remaining locked files."
        )

    try:
        log(f"Copying {source_folder} -> {target_folder}")
        copy_release_folder(source_folder, target_folder)
    except OSError as exc:
        show_popup(f"Copy failed:\n{exc}", is_error=True)
        return

    show_popup(f"Portable folder updated:\n{target_folder}")


if __name__ == "__main__":
    manage_folders()
