import os
import shutil
import json
from pathlib import Path


def load_extensions_from_manifest(manifest_path: str) -> tuple[list[dict], list[dict]]:
    """
    Load the include/exclude extension lists from a manifest JSON file.

    Args:
        manifest_path: Path to the manifest JSON file.

    Returns:
        (include_extensions, exclude_extensions): Two lists of dicts, e.g.:
            include_extensions = [{'name': 'ms-python.python', 'version': '2024.10.1'}, ...]
            exclude_extensions = [{'name': 'vscode-icons', 'version': '11.14.0'}, ...]
    """
    manifest_path = Path(manifest_path)

    if not manifest_path.exists():
        raise FileNotFoundError(f"Manifest file not found: {manifest_path}")

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    include_extensions = manifest.get("include_extensions", [])
    exclude_extensions = manifest.get("exclude_extensions", [])

    print(f"[ManifestLoader] Loaded {len(include_extensions)} included and {len(exclude_extensions)} excluded extensions.")
    return include_extensions, exclude_extensions


def apply_replace_mode(mode: str, backup_dir: str, temp_dir: str,
                      include_extensions: list[dict], exclude_extensions: list[dict],
                      target_dir: str) -> None:
    """
    Apply the specified replace mode to handle existing extensions.

    Args:
        mode: Replace mode - 'none', 'prune', or 'nuke'
        backup_dir: Directory to store backups
        temp_dir: Temporary directory for processing
        include_extensions: List of extensions to include in deployment
        exclude_extensions: List of extensions to exclude from deployment
        target_dir: Target VSCode extensions directory

    Replace modes:
    - 'none': Do not replace existing extensions
    - 'prune': Replace existing extensions that are not the same version
    - 'nuke': Replace all existing extensions
    """

    os.makedirs(backup_dir, exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)

    target_dir = Path(target_dir)
    temp_dir = Path(temp_dir)
    backup_dir = Path(backup_dir)

    print(f"[BackupManager] Starting apply_replace_mode('{mode}')")

    # --- Step 1: Backup current extensions ---
    print(f"[BackupManager] Backing up existing extensions → {backup_dir}")
    for ext_dir in target_dir.iterdir():
        dest = backup_dir / ext_dir.name
        if ext_dir.is_dir():
            shutil.copytree(ext_dir, dest, dirs_exist_ok=True)
    print("[BackupManager] ✅ Backup complete.")

    # --- Step 2: Handle 'nuke' mode (delete everything first) ---
    if mode == "nuke":
        print("[BackupManager] 🔥 Nuking all existing extensions.")
        shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

    # --- Step 3: Iterate over included extensions ---
    include_names = {ext['name'] for ext in include_extensions}
    exclude_names = {ext['name'] for ext in exclude_extensions}

    for ext in include_extensions:
        name, version = ext.get('name'), ext.get('version')
        if name in exclude_names:
            print(f"[BackupManager] ⚠ Skipping excluded extension: {name}")
            continue

        new_ext_dir = temp_dir / name
        existing_ext_dir = target_dir / name

        if not new_ext_dir.exists():
            print(f"[BackupManager] ⚠ Missing new extension folder for: {name}")
            continue

        if mode == "none" and existing_ext_dir.exists():
            print(f"[BackupManager] ⏩ Skipping existing extension (mode=none): {name}")
            continue

        if mode == "prune" and existing_ext_dir.exists():
            # Try reading version file (if present)
            existing_version = None
            version_file = existing_ext_dir / "package.json"
            if version_file.exists():
                try:
                    with open(version_file, "r") as f:
                        existing_version = json.load(f).get("version")
                except Exception:
                    pass

            if existing_version == version:
                print(f"[BackupManager] ⏩ Same version exists, skipping: {name}")
                continue
            else:
                print(f"[BackupManager] 🔁 Replacing outdated version of {name}")
                shutil.rmtree(existing_ext_dir, ignore_errors=True)

        # Copy from temp → target
        shutil.copytree(new_ext_dir, existing_ext_dir, dirs_exist_ok=True)
        print(f"[BackupManager] ✅ Deployed extension: {name} ({version})")

    print("[BackupManager] ✅ apply_replace_mode complete.")
