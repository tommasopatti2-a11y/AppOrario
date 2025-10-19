from __future__ import annotations
import re
import shutil
import zipfile
from pathlib import Path
from typing import Iterable

from .config import settings

SAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


def sanitize_filename(name: str) -> str:
    # Remove path separators and unsafe chars
    name = name.replace("\\", "/").split("/")[-1]
    name = SAFE_CHARS.sub("_", name)
    return name[:200]


def ensure_session_dirs(session_id: str) -> tuple[Path, Path, Path]:
    base = settings.OUTPUT_DIR_BASE / "sessions" / session_id
    inputs = base / "inputs"
    jobs = base / "jobs"
    for p in (base, inputs, jobs):
        p.mkdir(parents=True, exist_ok=True)
    return base, inputs, jobs


def create_job_dir(session_id: str, job_id: str) -> Path:
    base, _inputs, _jobs = ensure_session_dirs(session_id)
    workdir = base / "jobs" / job_id
    workdir.mkdir(parents=True, exist_ok=True)
    return workdir


def total_size(paths: Iterable[Path]) -> int:
    total = 0
    for p in paths:
        if p.is_file():
            total += p.stat().st_size
    return total


def zip_directory(src: Path, dest_zip: Path) -> None:
    dest_zip = dest_zip.resolve()
    with zipfile.ZipFile(dest_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in src.rglob("*"):
            if not file.is_file():
                continue
            # Skip the destination zip itself if it's under src
            if file.resolve() == dest_zip:
                continue
            zf.write(file, arcname=file.relative_to(src))


def list_files(dirpath: Path) -> list[dict]:
    files = []
    for f in sorted([p for p in dirpath.rglob('*') if p.is_file()]):
        files.append({
            "filename": str(f.relative_to(dirpath)).replace("\\", "/"),
            "size_bytes": f.stat().st_size,
        })
    return files


def cleanup_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
