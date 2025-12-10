from __future__ import annotations

import hashlib
import json
import zipfile
import subprocess
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator
from logging import Logger

_CHUNK_SIZE = 131072  # 128 KiB

@dataclass(frozen=True)
class ManifestEntry:
    member: str
    size: int | None
    sha256: str | None

    @classmethod
    def from_manifest(cls, idx: int, raw: dict) -> ManifestEntry | None:
        if raw.get("present", True) is False:
            return None

        raw_name = raw.get("path") or raw.get("name")
        if not isinstance(raw_name, str) or not raw_name.strip():
            raise ValueError(f"Manifest entry at index {idx} missing 'name'/'path'.")

        member = _ensure_safe_member(raw_name)
        size = raw.get("size")
        if size is not None:
            if not isinstance(size, int) or size < 0:
                raise ValueError(f"{member}: Manifest size must be a non-negative integer.")
        sha = raw.get("sha256")
        if sha is not None:
            sha = sha.strip().lower() or None
        return cls(member=member, size=size, sha256=sha)

    def verify(self, zf: zipfile.ZipFile) -> Iterator[str]:
        info = zf.getinfo(self.member)

        if self.size is not None and info.file_size != self.size:
            yield f"{self.member}: Size mismatch (expected {self.size}, got {info.file_size})."

        if not self.sha256:
            yield f"{self.member}: Manifest missing SHA-256 hash for verification."
            return

        actual = _hash_zip_member(zf, self.member)
        if actual != self.sha256:
            yield f"{self.member}: SHA-256 mismatch (expected {self.sha256}, got {actual})."


def expand_and_verify(archive: str, manifest: str, target_dir: str,
                      verify_integrity: str, dry_run: bool, logger: Logger | None = None) -> None:
    """
    Expand the archive and verify extension integrity.

    Args:
        archive: Path to the extensions archive file
        manifest: Path to the manifest file
        target_dir: Target directory for deployment
        verify_integrity: Verification mode - 'ERROR', 'NONE', or 'WARN'
        dry_run: Whether to perform a dry run (no actual changes)

    Verification modes:
    - 'ERROR': Fail if integrity is not correct
    - 'NONE': Do not verify integrity
    - 'WARN': Warn if integrity is not correct but continue
    """
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()
    
    mode = (verify_integrity or "NONE").upper()
    archive_path = Path(archive).expanduser().resolve()
    manifest_path = Path(manifest).expanduser().resolve()
    target_path = Path(target_dir).expanduser().resolve()
    should_extract = not bool(dry_run)

    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    entries = _read_manifest(manifest_path)
    if not entries:
        logger.info("Manifest contains no present files; nothing to do.")
        return

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            _ensure_members_present(zf, entries, archive_path)

            if mode != "NONE":
                findings = list(_verify_entries(zf, entries))
                if findings:
                    _handle_verification_findings(mode, findings, logger)
                else:
                    logger.info(f"Integrity check passed for {len(entries)} file(s).")

            if not should_extract:
                logger.info("Dry run enabled - skipping extraction after verification.")
                return

            target_path.mkdir(parents=True, exist_ok=True)
            zf.extractall(path=target_path, members=[entry.member for entry in entries])
            logger.info(f"Extracted {len(entries)} file(s) into {target_path.resolve()}.")

    except zipfile.BadZipFile as exc:
        raise ValueError(f"Archive at {archive_path} is not a valid ZIP file.") from exc


def _read_manifest(path: Path) -> list[ManifestEntry]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    files = data.get("files")
    if not isinstance(files, list):
        raise ValueError("Manifest missing 'files' array or array is invalid.")

    entries: list[ManifestEntry] = []
    for idx, raw in enumerate(files):
        entry = ManifestEntry.from_manifest(idx, raw)
        if entry:
            entries.append(entry)
    return entries


def _ensure_members_present(zf: zipfile.ZipFile,
                            entries: Iterable[ManifestEntry],
                            archive_path: Path) -> None:
    available = set(zf.namelist())
    missing = sorted(entry.member for entry in entries if entry.member not in available)
    if missing:
        raise FileNotFoundError(
            f"Archive {archive_path} is missing expected file(s): {', '.join(missing)}"
        )


def _verify_entries(zf: zipfile.ZipFile, entries: Iterable[ManifestEntry]) -> Iterator[str]:
    for entry in entries:
        yield from entry.verify(zf)


def _hash_zip_member(zf: zipfile.ZipFile, member: str) -> str:
    digest = hashlib.sha256()
    with zf.open(member, "r") as source:
        for chunk in iter(lambda: source.read(_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _ensure_safe_member(value: str) -> str:
    candidate = value.strip()
    if not candidate:
        raise ValueError("Manifest entry has an empty path/name.")
    if candidate.startswith(("/", "\\")):
        raise ValueError(f"Manifest entry path must be relative: {value!r}")
    if ":" in candidate:
        raise ValueError(f"Manifest entry path contains invalid character ':' ({value!r}).")

    normalized = candidate.replace("\\", "/")
    parts = [part for part in normalized.split("/") if part]
    if any(part == ".." for part in parts):
        raise ValueError(f"Manifest entry path escapes target directory: {value!r}")
    return "/".join(parts)


def _handle_verification_findings(mode: str, findings: Iterable[str], logger: Logger | None = None) -> None:
    message = "Integrity verification found issues:\n" + "\n".join(
        f" - {issue}" for issue in findings
    )
    if mode == "ERROR":
        raise ValueError(message)
    if logger:
        logger.warning(message)


def install_extensions(manifest: str, target_dir: str, commit_id: str | None = None,
                       dry_run: bool = False, logger: Logger | None = None) -> None:
    """
    Install VSIX extensions using the VS Code server's code CLI.
    
    Args:
        manifest: Path to the manifest file (to get list of VSIX files)
        target_dir: Directory where VSIX files were extracted
        commit_id: VS Code server commit ID (to locate the code CLI)
        dry_run: Whether to perform a dry run (no actual installation)
        logger: Logger instance
    """
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()
    
    if dry_run:
        logger.info("Dry run enabled - skipping extension installation.")
        return
    
    # Find the code CLI
    code_cli_path = _find_code_cli(commit_id, logger)
    if not code_cli_path:
        logger.warning("Could not find VS Code server code CLI; skipping extension installation.")
        logger.warning("Extensions were extracted but not installed. You may need to install them manually.")
        return
    
    # Read manifest to get list of VSIX files
    manifest_path = Path(manifest).expanduser().resolve()
    if not manifest_path.is_file():
        logger.warning(f"Manifest not found: {manifest_path}; skipping extension installation.")
        return
    
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
    except Exception as e:
        logger.warning(f"Failed to read manifest: {e}; skipping extension installation.")
        return
    
    files = manifest_data.get("files", [])
    vsix_files = []
    for file_entry in files:
        if file_entry.get("present", True) is False:
            continue
        file_path = file_entry.get("path") or file_entry.get("name")
        if file_path and file_path.endswith(".vsix"):
            vsix_files.append(file_path)
    
    if not vsix_files:
        logger.info("No VSIX files found in manifest; nothing to install.")
        return
    
    target_path = Path(target_dir).expanduser().resolve()
    installed_count = 0
    failed_count = 0
    
    for vsix_file in vsix_files:
        vsix_path = target_path / vsix_file
        if not vsix_path.exists():
            logger.warning(f"VSIX file not found: {vsix_path}; skipping.")
            failed_count += 1
            continue
        
        try:
            logger.info(f"Installing extension: {vsix_path.name}")
            result = subprocess.run(
                [str(code_cli_path), "--install-extension", str(vsix_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout per extension
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Successfully installed: {vsix_path.name}")
                installed_count += 1
                # Optionally remove the VSIX file after successful installation
                # vsix_path.unlink()
            else:
                logger.warning(f"❌ Failed to install {vsix_path.name}: {result.stderr}")
                failed_count += 1
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing {vsix_path.name}")
            failed_count += 1
        except Exception as e:
            logger.error(f"Error installing {vsix_path.name}: {e}")
            failed_count += 1
    
    logger.info(f"Extension installation complete: {installed_count} installed, {failed_count} failed")


def _find_code_cli(commit_id: str | None = None, logger: Logger | None = None) -> Path | None:
    """
    Find the VS Code server's code CLI executable.
    
    Args:
        commit_id: VS Code server commit ID (optional, will try to find any installed server)
        logger: Logger instance
    
    Returns:
        Path to the code CLI executable, or None if not found
    """
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()
    
    home = Path.home()
    vscode_server_bin = home / ".vscode-server" / "bin"
    
    if not vscode_server_bin.exists():
        logger.debug(f"VS Code server bin directory not found: {vscode_server_bin}")
        return None
    
    # Possible locations for the code CLI
    possible_paths = [
        "bin/code",           # Standard location
        "code",                # Root of server directory
        "bin/code-server",     # Alternative name
    ]
    
    # If commit_id is provided, try that specific commit first
    if commit_id:
        server_dir = vscode_server_bin / commit_id
        if server_dir.exists():
            for rel_path in possible_paths:
                code_cli = server_dir / rel_path
                if code_cli.exists() and os.access(code_cli, os.X_OK):
                    logger.debug(f"Found code CLI at: {code_cli}")
                    return code_cli
    
    # Otherwise, try to find any installed server
    for commit_dir in sorted(vscode_server_bin.iterdir(), reverse=True):  # Try newest first
        if not commit_dir.is_dir():
            continue
        for rel_path in possible_paths:
            code_cli = commit_dir / rel_path
            if code_cli.exists() and os.access(code_cli, os.X_OK):
                logger.debug(f"Found code CLI at: {code_cli}")
                return code_cli
    
    logger.debug("Could not find code CLI in any VS Code server installation")
    return None

