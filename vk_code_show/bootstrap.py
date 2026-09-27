from __future__ import annotations

import os
import sys
from pathlib import Path


def run() -> int:
    ensure_project_environment()
    if "--smoke-test" in sys.argv:
        from .smoke import run as smoke_run
        index = sys.argv.index("--smoke-test")
        return smoke_run(Path(sys.argv[index + 1]).resolve())

    try:
        from .app import main
    except ModuleNotFoundError as error:
        if error.name == "PySide6":
            print(missing_pyside6_message(), file=sys.stderr)
            return 1
        raise

    return main()


def ensure_project_environment() -> None:
    venv_python = project_venv_python()
    if venv_python is None or is_current_python(venv_python):
        return

    root_script = project_root() / f"{project_root().name}.py"
    script = root_script if root_script.exists() else Path(sys.argv[0]).resolve()
    os.execv(str(venv_python), [str(venv_python), str(script), *sys.argv[1:]])


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_venv_python() -> Path | None:
    root = project_root()
    if os.name == "nt":
        candidate = root / ".venv" / "Scripts" / "python.exe"
    else:
        candidate = root / ".venv" / "bin" / "python"
    return candidate if candidate.exists() else None


def is_current_python(candidate: Path) -> bool:
    current = Path(sys.executable).resolve()
    target = candidate.resolve()
    try:
        return current.samefile(target)
    except OSError:
        return current == target


def missing_pyside6_message() -> str:
    return (
        "PySide6 не установлен в текущем окружении Python.\n"
        "Запустите приложение через проектную виртуальную среду:\n\n"
        "  .\\.venv\\Scripts\\python.exe .\\VK-code-show.py\n\n"
        "Если виртуальной среды нет, сначала создайте ее:\n\n"
        "  py -3.12 -m venv .venv\n"
        "  .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt"
    )
