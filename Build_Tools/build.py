"""Reproducible build entry point, shared by CLI and GUI builder."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from runtime_dll_policy import minimal_path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    if Path(sys.prefix).resolve() != root / ".venv":
        raise RuntimeError("Build requires the project .venv")
    old = (root / "VK-code-show").resolve()
    if old.parent != root or old.is_symlink():
        raise RuntimeError(f"Unsafe build target: {old}")
    if old.exists():
        backup = root / "_release_work" / "pre-build-settings"
        backup.mkdir(parents=True, exist_ok=True)
        for name in ("settings.json", ".env"):
            if (old / name).is_file():
                shutil.copy2(old / name, backup / name)
        shutil.rmtree(old)
    env = dict(os.environ, PATH=minimal_path())
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            str(root / "Build_Tools/VK-code-show.spec"),
            "--clean",
            "--noconfirm",
            "--distpath",
            str(root / "Build_Tools/dist"),
            "--workpath",
            str(root / "Build_Tools/build"),
        ],
        cwd=root,
        env=env,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(root / "Build_Tools/post_build.py")],
        cwd=root,
        env=env,
        check=True,
    )


if __name__ == "__main__":
    main()
