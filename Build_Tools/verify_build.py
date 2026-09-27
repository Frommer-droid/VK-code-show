"""Verify COLLECT origins and execute the actual EXE in an isolated Qt smoke mode."""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from runtime_dll_policy import MSVC_NAMES, minimal_path, validate_origins


def verify(project_root: Path, app_dir: Path) -> dict:
    import PySide6

    toc_paths = [
        project_root / "Build_Tools/build/VK-code-show/COLLECT-00.toc",
        project_root / "build/VK-code-show/COLLECT-00.toc",
    ]
    toc = next((path for path in toc_paths if path.is_file()), None)
    if toc is None:
        raise RuntimeError("COLLECT-00.toc is required before post-build cleanup")
    entries = ast.literal_eval(toc.read_text(encoding="utf-8"))[-1]
    validate_origins(entries, project_root)
    native = [entry for entry in entries if entry[2] in {"BINARY", "EXTENSION"}]
    qt_dir = Path(PySide6.__file__).resolve().parent

    def digest(path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    for name in MSVC_NAMES:
        if digest(app_dir / "_internal" / name) != digest(qt_dir / name):
            raise RuntimeError(f"MSVC runtime differs from Qt: {name}")
    reports = project_root / "_release_work"
    reports.mkdir(exist_ok=True)
    report_path = reports / "frozen-smoke.json"
    report_path.unlink(missing_ok=True)
    env = dict(os.environ, PATH=minimal_path(), QT_QPA_PLATFORM="offscreen")
    result = subprocess.run(
        [str(app_dir / "VK-code-show.exe"), "--smoke-test", str(report_path)],
        env=env,
        cwd=app_dir,
        capture_output=True,
        text=True,
        timeout=45,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    report = (
        json.loads(report_path.read_text(encoding="utf-8"))
        if report_path.exists()
        else {}
    )
    if result.returncode or not report.get("ok") or not report.get("frozen"):
        raise RuntimeError(
            f"Frozen smoke failed: {result.returncode}\n"
            f"{result.stdout}\n{result.stderr}\n{report}"
        )
    if "Traceback" in result.stdout + result.stderr or "ERROR" in result.stderr:
        raise RuntimeError(f"Frozen diagnostics: {result.stdout}\n{result.stderr}")
    if report["version"] != (project_root / "VERSION").read_text().strip():
        raise RuntimeError("Frozen version does not match VERSION")
    audit = {
        "foreign_origins": 0,
        "native_files": len(native),
        "qt_msvc_hashes_match": True,
        "smoke": report,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "exit_code": result.returncode,
        "executable_sha256": digest(app_dir / "VK-code-show.exe"),
        "binary_origins": native,
    }
    (reports / "build-audit.json").write_text(
        json.dumps(audit, indent=2), encoding="utf-8"
    )
    print(
        f"Build verified: {len(native)} native files, zero foreign origins, frozen smoke OK"
    )
    return audit


if __name__ == "__main__":
    verify(Path(__file__).resolve().parent.parent, Path(sys.argv[1]).resolve())
