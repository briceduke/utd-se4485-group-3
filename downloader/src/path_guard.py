from __future__ import annotations
import os, shutil
from dataclasses import dataclass
from pathlib import Path

class PathGuardError(RuntimeError):
    pass

@dataclass(frozen=True)
class Paths:
    cache_dir: Path
    work_dir: Path
    vsix_out_dir: Path
    output_zip: Path
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

def ensure_paths(cache_dir: str, output_zip: str, log_file: str | None = None) -> GuardResult:
    cache = Path(cache_dir).expanduser().resolve()
    outzip = Path(output_zip).expanduser().resolve()
    logf = Path(log_file).expanduser().resolve() if log_file else None

    _must_abs(cache, "cache_dir")
    _must_abs(outzip, "output_zip")
    if logf: _must_abs(logf, "log_file")

    work = cache / "builder_work"
    vsix = cache / "vsix_norm"

    _writable_dir(cache)
    _writable_dir(work)
    _writable_dir(vsix)
    _writable_dir(outzip.parent)
    if logf: _writable_dir(logf.parent)

    warns = []
    try:
        free = shutil.disk_usage(cache).free
        if free < 50 * 1024 * 1024:
            warns.append(f"Low free space under {cache}: {free} bytes")
    except Exception:
        pass

    return GuardResult(Paths(cache, work, vsix, outzip, logf), tuple(warns))

def validate_code_cli(code_cli_path: str | None) -> tuple[str | None, tuple[str, ...]]:
    warns = []
    if not code_cli_path:
        return None, ("No code CLI configured; some steps may fail.",)
    p = Path(code_cli_path)
    if p.is_absolute():
        if not p.exists(): return None, (f"code CLI not found: {p}",)
        if not os.access(p, os.X_OK): warns.append(f"code CLI not executable: {p}")
        return str(p), tuple(warns)
    found = shutil.which(code_cli_path)
    if not found: return None, (f"'{code_cli_path}' not found in PATH",)
    return found, tuple(warns)
