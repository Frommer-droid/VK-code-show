"""Fail closed on foreign native libraries; select the complete Qt MSVC runtime."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import PySide6
import shiboken6

MSVC_NAMES = (
    "concrt140.dll",
    "msvcp140.dll",
    "msvcp140_1.dll",
    "msvcp140_2.dll",
    "msvcp140_codecvt_ids.dll",
    "vcruntime140.dll",
    "vcruntime140_1.dll",
)


def minimal_path() -> str:
    paths = [
        Path(PySide6.__file__).parent,
        Path(shiboken6.__file__).parent,
        Path(sys.prefix) / "Scripts",
        Path(sys.base_prefix),
        Path(sys.base_prefix) / "DLLs",
        Path(os.environ["SystemRoot"]) / "System32",
    ]
    return os.pathsep.join(str(path.resolve()) for path in paths)


def validate_origins(entries, project_root: Path) -> None:
    roots = [
        project_root.resolve(),
        Path(sys.prefix).resolve(),
        Path(sys.base_prefix).resolve(),
        Path(os.environ["SystemRoot"]).resolve(),
    ]
    for destination, source, kind in entries:
        if kind not in {"BINARY", "EXTENSION"}:
            continue
        path = Path(source).resolve()
        if not any(path.is_relative_to(root) for root in roots):
            raise RuntimeError(f"Untrusted native origin: {destination} <- {path}")


def qt_runtime(entries, project_root: Path):
    # Validate BEFORE replacement: never hide a foreign runtime DLL.
    validate_origins(entries, project_root)
    qt_dir = Path(PySide6.__file__).resolve().parent
    names = set(MSVC_NAMES)
    result = [entry for entry in entries if Path(entry[0]).name.lower() not in names]
    for name in MSVC_NAMES:
        source = qt_dir / name
        if not source.is_file():
            raise RuntimeError(f"Missing required Qt runtime DLL: {source}")
        result.append((name, str(source), "BINARY"))
    validate_origins(result, project_root)
    return result
