from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple, List
from logging import Logger


def build_zip_and_manifest(files: List[str], output_dir: str,
                          name_template: str, logger: Logger | None = None) -> Tuple[str, str]:
    """Build a ZIP archive and a JSON manifest for a list of files.

    Args:
        files: List of paths to downloaded extension files
        output_dir: Directory where the output files should be saved
        name_template: Template for naming the output files (e.g., 'everfox-extensions-{{date}}.zip')

    Returns:
        Tuple of (zip_path, manifest_path) containing paths to created files

    The name_template may contain the placeholder ``{{date}}`` which will be
    substituted with the current UTC date in YYYYMMDD format. If the
    resulting name does not end with ``.zip`` the suffix will be added.
    A manifest JSON with the same base name and a ``.json`` extension will
    be written alongside the ZIP file. The manifest contains per-file
    metadata including filename, size (bytes) and sha256.
    """
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()

    # Convert output directory string to Path object for easier path manipulation
    out_dir = Path(output_dir)
    
    # Create output directory and any parent directories if they don't exist
    # exist_ok=True prevents errors if directory already exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Get current UTC date and format as YYYYMMDD (e.g., "20251025")
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # Replace {{date}} placeholder in template with actual date
    # Example: "everfox-extensions-{{date}}.zip" becomes "everfox-extensions-20251025.zip"
    rendered = name_template.replace("{{date}}", date_str)

    # Ensure the rendered filename ends with .zip extension
    # Case-insensitive check to handle .ZIP, .Zip, etc.
    if not rendered.lower().endswith(".zip"):
        rendered = f"{rendered}.zip"

    # Construct full path for ZIP file (directory + filename)
    zip_path = out_dir / rendered
    
    # Construct manifest path using same base name but .json extension
    # zip_path.stem gives filename without extension
    manifest_path = out_dir / (zip_path.stem + ".json")

    logger.info(f"Building archive: {zip_path}")

    # Capture current timestamp in ISO 8601 format for manifest metadata
    # Example: "2025-10-25T14:30:45.123456+00:00"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Initialize list to store metadata for each file
    manifest_entries = []

    # Create ZIP archive with DEFLATE compression (standard compression algorithm)
    # Using context manager ensures ZIP is properly closed even if errors occur
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Iterate through each file path (or empty list if files is None)
        for f in files or []:
            # Convert file path string to Path object
            src = Path(f)
            
            # Check if the source file actually exists on disk
            if not src.exists():
                # File is missing - add entry to manifest marking it as not present
                # This allows tracking what should have been included but wasn't found
                manifest_entries.append({
                    "name": src.name,          # Filename only
                    "path": str(src),          # Original full path that was requested
                    "present": False,          # Flag indicating file was not found
                })
                continue  # Skip to next file

            # Extract just the filename (no directory path) for storage in ZIP
            # This flattens the directory structure - all files go in ZIP root
            arcname = src.name
            
            # Add file to ZIP archive using the archive name (filename only)
            # str(src) converts Path to string for zipfile compatibility
            zf.write(str(src), arcname=arcname)

            # Compute SHA-256 hash for file integrity verification
            # Initialize hash object
            sha256 = hashlib.sha256()
            
            # Read file in binary mode and hash in chunks to handle large files efficiently
            # Using 8KB chunks to balance memory usage and I/O performance
            with src.open("rb") as fh:
                # Read chunks until empty bytes returned (end of file)
                for chunk in iter(lambda: fh.read(8192), b""):
                    sha256.update(chunk)  # Update hash with current chunk

            # Get file metadata (size, modification time, etc.)
            stat = src.stat()
            
            # Add complete metadata entry for this file to manifest
            manifest_entries.append({
                "name": arcname,                    # Filename as stored in ZIP
                "path": arcname,                    # Path within ZIP (same as name since flattened)
                "size": stat.st_size,               # File size in bytes
                "sha256": sha256.hexdigest(),       # SHA-256 hash as hexadecimal string
                "mtime": datetime.fromtimestamp(    # File modification time in ISO 8601 format
                    stat.st_mtime, timezone.utc
                ).isoformat(),
                "present": True,                    # Flag indicating file was successfully included
            })

    # Build complete manifest structure with metadata and file list
    manifest = {
        "generated_at": now_iso,        # Timestamp when manifest was created
        "zip": str(zip_path),            # Full path to the ZIP file
        "files": manifest_entries,       # List of all file metadata entries
    }

    # Write manifest to JSON file with pretty formatting
    # indent=2 with 2-space indentation
    # ensure_ascii=False allows Unicode characters in filenames
    with manifest_path.open("w", encoding="utf-8") as mf:
        json.dump(manifest, mf, indent=2, ensure_ascii=False)

    logger.info(f"Created manifest: {manifest_path}")

    # Delete the files after the zip is created
    for f in files:
        if Path(f).exists():
            Path(f).unlink()

    logger.info(f"Packaged {len(files or [])} extension(s)")

    # Return paths as strings (convert Path objects back to strings)
    return str(zip_path), str(manifest_path)

