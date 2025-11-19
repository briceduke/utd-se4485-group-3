from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Iterator

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
                      verify_integrity: str, dry_run: bool) -> None:
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
    mode = (verify_integrity or "NONE").upper()
    archive_path = Path(archive).expanduser()
    manifest_path = Path(manifest).expanduser()
    target_path = Path(target_dir).expanduser()
    should_extract = not bool(dry_run)

    if not archive_path.is_file():
        raise FileNotFoundError(f"Archive not found: {archive_path}")
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}")

    entries = _read_manifest(manifest_path)
    if not entries:
        _say("INFO", "Manifest contains no present files; nothing to do.")
        return

    try:
        with zipfile.ZipFile(archive_path, "r") as zf:
            _ensure_members_present(zf, entries, archive_path)

            if mode != "NONE":
                findings = list(_verify_entries(zf, entries))
                if findings:
                    _handle_verification_findings(mode, findings)
                else:
                    _say("INFO", "Integrity check passed for %d file(s).", len(entries))

            if not should_extract:
                _say("INFO", "Dry run enabled - skipping extraction after verification.")
                return

            target_path.mkdir(parents=True, exist_ok=True)
            zf.extractall(path=target_path, members=[entry.member for entry in entries])
            _say("INFO", "Extracted %d file(s) into %s.", len(entries), target_path.resolve())

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


def _handle_verification_findings(mode: str, findings: Iterable[str]) -> None:
    message = "Integrity verification found issues:\n" + "\n".join(
        f" - {issue}" for issue in findings
    )
    if mode == "ERROR":
        raise ValueError(message)
    _say("WARN", message)


def _say(level: str, message: str, *args) -> None:
    if args:
        message = message % args
    print(f"[{level}] {message}")
