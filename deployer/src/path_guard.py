from __future__ import annotations
import os, shutil
from dataclasses import dataclass
from pathlib import Path

class PathGuardError(RuntimeError):
    pass

@dataclass(frozen=True)
class Paths:
    backup_dir: Path
    temp_dir: Path
    target_dir: Path
    log_file: Path | None = None

@dataclass(frozen=True)
class GuardResult:
    paths: Paths
    warnings: tuple[str, ...] = ()

def _must_abs(p: Path, label: str):
    if not p.is_absolute():
        raise PathGuardError(f"{label} must be an absolute path: {p}")

def _writable_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)
    if not p.is_dir():
        raise PathGuardError(f"Not a directory: {p}")
    test = p / ".wcheck"
    test.write_text("ok")
    test.unlink(missing_ok=True)

def ensure_paths(backup_dir: str, temp_dir: str, target_dir: str, log_file: str | None = None) -> GuardResult:
    backup = Path(backup_dir).expanduser().resolve()
    temp = Path(temp_dir).expanduser().resolve()
    target = Path(target_dir).expanduser().resolve()
    logf = Path(log_file).expanduser().resolve() if log_file else None

    _must_abs(backup, "backup_dir")
    _must_abs(temp, "temp_dir")
    _must_abs(target, "target_dir")
    if logf: _must_abs(logf, "log_file")

    _writable_dir(backup)
    _writable_dir(temp)
    _writable_dir(target)
    if logf: _writable_dir(logf.parent)

    warns = []
    try:
        free = shutil.disk_usage(backup).free
        if free < 100 * 1024 * 1024:
            warns.append(f"Low free space under {backup}: {free} bytes")
    except Exception:
        pass

    return GuardResult(Paths(backup, temp, target, logf), tuple(warns))
