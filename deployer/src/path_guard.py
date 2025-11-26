# deployer/src/path_guard.py
from __future__ import annotations
from pathlib import Path
import os

def _is_probably_file(p: Path) -> bool:
    """
    Heuristic:
    - If it exists and is a file -> True
    - Else if it has a suffix (e.g., *.log, *.json, *.zip) -> True
    - Else -> treat as directory
    """
    try:
        if p.exists() and p.is_file():
            return True
    except Exception:
        pass
    return bool(p.suffix)

def _ensure_writable_dir(d: Path) -> None:
    d.mkdir(parents=True, exist_ok=True)
    if not os.access(d, os.W_OK):
        raise PermissionError(f"Directory is not writable: {d}")

def ensure_paths(paths: list[str | os.PathLike[str]]) -> None:
    """
    For each path:
      - If it looks like a file path, ensure the parent directory exists and is writable
      - Otherwise, ensure the directory itself exists and is writable
    Raises PermissionError if a directory is not writable.
    """
    for raw in paths:
        if not raw:
            continue
        p = Path(raw).expanduser()

        if _is_probably_file(p):
            parent = p.parent if p.parent != Path("") else Path(".")
            _ensure_writable_dir(parent)
        else:
            _ensure_writable_dir(p)
