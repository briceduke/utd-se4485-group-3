from __future__ import annotations

import json
import shutil
import re
from datetime import datetime
from pathlib import Path
from logging import Logger

MANIFEST_FILENAME = "manifest.json"
_VERSION_TOKEN = re.compile(r"^(latest|v?\d[\w.\-]*)$", re.IGNORECASE)


def apply_replace_mode(mode: str, backup_dir: str, temp_dir: str,
                       include_extensions: list[dict], exclude_extensions: list[dict],
                       target_dir: str, logger: Logger | None = None) -> None:
    """
    Apply the specified replace mode to handle existing extensions.

    Args:
        mode: Replace mode - 'NONE', 'REPLACE', or 'CLEAN'
        backup_dir: Directory to store backups
        temp_dir: Temporary directory for processing
        include_extensions: List of extensions to include in deployment
        exclude_extensions: List of extensions to exclude from deployment
        target_dir: Target VSCode extensions directory

    Replace modes:
    - 'NONE': Do not replace existing extensions
    - 'REPLACE': Replace existing extensions that are not the same version
    - 'CLEAN': Replace all existing extensions
    """
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()
    
    normalized = (mode or "NONE").upper()
    if normalized not in {"NONE", "REPLACE", "CLEAN"}:
        raise ValueError(f"Unsupported replace mode: {mode}")

    target = Path(target_dir).expanduser()
    backup = Path(backup_dir).expanduser()
    temp = Path(temp_dir).expanduser()

    target.mkdir(parents=True, exist_ok=True)
    temp.mkdir(parents=True, exist_ok=True)
    backup.mkdir(parents=True, exist_ok=True)

    if _is_within(backup, target):
        raise ValueError("Backup directory cannot be inside the target directory.")

    if normalized == "NONE":
        logger.debug("Replace mode NONE - skipping backup and cleanup.")
        return

    installed = _scan_extensions(target)
    if not installed:
        logger.info(f"No extensions found in {target}; nothing to {normalized.lower()}.")
        return

    manifest = _load_manifest(temp / MANIFEST_FILENAME)
    desired = _select_manifest_entries(manifest, include_extensions, exclude_extensions)

    victims = installed if normalized == "CLEAN" else _changed(installed, desired)
    if not victims:
        logger.info("All installed extensions already match desired versions.")
        return

    _backup_and_remove(victims, backup, normalized, logger)


def _scan_extensions(target: Path) -> list[dict]:
    extensions: list[dict] = []
    for item in target.iterdir():
        if item.name.startswith("."):
            continue
        if not (item.is_dir() or item.suffix.lower() == ".vsix"):
            continue
        ident, version = _split_name(item.name)
        if not ident:
            continue
        extensions.append({"id": ident, "version": version, "path": item})
    return extensions


def _load_manifest(manifest_path: Path) -> list[dict]:
    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found at {manifest_path}")
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    picked: list[dict] = []
    for file_info in data.get("files", []):
        if file_info.get("present", True) is False:
            continue
        name = file_info.get("name") or file_info.get("path")
        ident, version = _split_name(name or "")
        if ident:
            picked.append({"id": ident, "version": version})
    return picked


def _select_manifest_entries(entries: list[dict],
                             include_rules: list[dict],
                             exclude_rules: list[dict]) -> dict[str, str | None]:
    include = _normalize_rules(include_rules)
    exclude = _normalize_rules(exclude_rules)
    selected: dict[str, str | None] = {}
    for entry in entries:
        name = entry["id"]
        version = entry["version"]
        if exclude and any(_rule_matches(rule, name, version) for rule in exclude):
            continue
        if include and not any(_rule_matches(rule, name, version) for rule in include):
            continue
        selected[name] = version
    return selected if selected or not include else {}


def _normalize_rules(rules: list[dict] | None) -> list[tuple[str, str | None]]:
    normalized: list[tuple[str, str | None]] = []
    for rule in rules or []:
        name = (rule.get("name") or "").strip().lower()
        if not name:
            continue
        version = _normalize_version(rule.get("version"))
        normalized.append((name, version))
    return normalized


def _changed(installed: list[dict], desired: dict[str, str | None]) -> list[dict]:
    victims: list[dict] = []
    for ext in installed:
        wanted = desired.get(ext["id"])
        if wanted is None:
            continue
        if _same_version(wanted, ext["version"]):
            continue
        victims.append(ext)
    return victims


def _backup_and_remove(victims: list[dict], backup_root: Path, mode: str, logger: Logger | None = None) -> None:
    session = _create_session_dir(backup_root, mode, logger)
    for ext in victims:
        src = ext["path"]
        dest = session / src.name
        if src.is_dir():
            shutil.copytree(src, dest)
            shutil.rmtree(src)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest)
            src.unlink()
        if logger:
            logger.debug(f"Moved {src} -> {dest}")
    if logger:
        logger.info(f"Backed up and removed {len(victims)} item(s) in {mode} mode.")


def _create_session_dir(base: Path, mode: str, logger: Logger | None = None) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    session = base / f"{timestamp}_{mode.lower()}"
    counter = 0
    while session.exists():
        counter += 1
        session = base / f"{timestamp}_{mode.lower()}_{counter}"
    session.mkdir(parents=True, exist_ok=False)
    if logger:
        logger.info(f"Created backup directory at {session}")
    return session


def _split_name(raw_name: str) -> tuple[str | None, str | None]:
    if not raw_name:
        return None, None
    leaf = Path(raw_name).name
    base = leaf[:-5] if leaf.lower().endswith(".vsix") else leaf
    parts = base.split("-")
    if len(parts) >= 2:
        suffix = parts[-1]
        if _VERSION_TOKEN.match(suffix):
            ident = "-".join(parts[:-1]).lower()
            return ident or None, suffix.lower()
    return base.lower(), None


def _normalize_version(value: str | None) -> str | None:
    if value is None:
        return None
    trimmed = value.strip().lower()
    return trimmed or None


def _same_version(a: str | None, b: str | None) -> bool:
    return _normalize_version(a) == _normalize_version(b)


def _rule_matches(rule: tuple[str, str | None], name: str, version: str | None) -> bool:
    rule_name, rule_version = rule
    if name != rule_name:
        return False
    if rule_version is None:
        return True
    return _same_version(rule_version, version)


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


