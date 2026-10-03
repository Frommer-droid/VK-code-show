# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
import sys
from importlib import metadata
from pathlib import Path


if sys.stdout:
    sys.stdout.reconfigure(encoding="utf-8")


APP_NAME = "VK-code-show"
FILES_TO_COPY = [
    ("logo.ico", "logo.ico"),
    ("VERSION", "VERSION"),
    ("LICENSE", "LICENSE"),
    ("THIRD_PARTY_NOTICES.md", "THIRD_PARTY_NOTICES.md"),
    ("RELEASE_NOTES.md", "RELEASE_NOTES.md"),
]


def safe_remove_tree(path: Path) -> None:
    root = Path(__file__).resolve().parent.parent
    path = path.resolve()
    if not path.is_relative_to(root) or path == root or path.is_symlink():
        raise ValueError(f"Unsafe cleanup target: {path}")
    if not path.exists():
        return
    shutil.rmtree(path)
    print(f"[OK] Removed: {path}")


def safe_copy(src: Path, dst: Path) -> None:
    if not src.exists():
        print(f"[SKIP] Not found: {src}")
        return
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    print(f"[OK] Copied: {src} -> {dst}")


def find_dist_app_dir(script_dir: Path, project_root: Path) -> Path | None:
    candidates = [
        script_dir / "dist" / APP_NAME,
        project_root / "dist" / APP_NAME,
    ]
    return next((path for path in candidates if path.exists()), None)


def package_version(package_name: str) -> str:
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "not-installed"


def write_runtime_manifest(project_root: Path, final_app_dir: Path) -> None:
    version_path = project_root / "VERSION"
    app_version = version_path.read_text(encoding="utf-8").strip() if version_path.exists() else "0.0.0"
    manifest = {
        "app_name": APP_NAME,
        "app_version": app_version,
        "python_version": sys.version.split()[0],
        "platform": sys.platform,
        "executable_sha256": __import__("hashlib").sha256(
            (final_app_dir / f"{APP_NAME}.exe").read_bytes()).hexdigest(),
        "frozen_smoke_verified": True,
        "packages": {
            "PySide6": package_version("PySide6"),
            "PyInstaller": package_version("PyInstaller"),
        },
    }
    import json

    (final_app_dir / "RUNTIME_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote: {final_app_dir / 'RUNTIME_MANIFEST.json'}")


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    dist_app_dir = find_dist_app_dir(script_dir, project_root)
    final_app_dir = project_root / APP_NAME

    print()
    print("=" * 60)
    print(f"POST BUILD: {APP_NAME}")
    print("=" * 60)

    if dist_app_dir is None:
        print(f"[ERROR] dist/{APP_NAME} was not found in Build_Tools or project root.")
        return 1

    from verify_build import verify
    verify(project_root, dist_app_dir)

    if final_app_dir.exists():
        safe_remove_tree(final_app_dir)
    shutil.move(str(dist_app_dir), str(final_app_dir))
    print(f"[OK] Moved build to: {final_app_dir}")

    for src_rel, dst_rel in FILES_TO_COPY:
        safe_copy(project_root / src_rel, final_app_dir / dst_rel)

    write_runtime_manifest(project_root, final_app_dir)

    temp_dirs = [
        script_dir / "build",
        script_dir / "dist",
        script_dir / "__pycache__",
        project_root / "build",
        project_root / "dist",
        project_root / "__pycache__",
        final_app_dir / "__pycache__",
    ]
    for temp_dir in temp_dirs:
        safe_remove_tree(temp_dir)

    exe_path = final_app_dir / f"{APP_NAME}.exe"
    if not exe_path.exists():
        print(f"[ERROR] Executable was not found: {exe_path}")
        return 1

    print()
    print("=" * 60)
    print(f"DONE: {exe_path}")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
