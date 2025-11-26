# Purpose:
#   Pre-seed the VS Code *server* on the remote machine (air-gapped target) 
#   from the bundle contents. This avoids the online fetch during first remote ssh connect.
#
# Reads from bundle: vscode-server/<commit>/server-linux-x64.tar.gz
# Installs to:          ~/.vscode-server/bin/<commit>/ (must contain server.sh, node, bin/code-server)


from __future__ import annotations
import tarfile
from pathlib import Path 

class RemoteServerError(RuntimeError):
    """Raised when the preseed cannot complete cleanly"""

def preseed_server(commit: str, bundle_root: Path, home: Path | None = None) -> Path:
    """
    Unpack the CS Code server tarball into the standard location and ensure server.sh is executable.

    Args:
        commit: VS Code client commit hash (from 'code --version' on the client)
        bundle_root: path where the deployer already expanded the extensions bundle ZIP. 
                    Expected structure: bundle_root/vscode-server/<commit>/server-linux-x64.tar.gz
        home: (optional) override for home dir. Defaults to Path.home().
    
    Returns: 
        Path to the installed commit directory
    
    Raises:
        RemoteServerError if the tarball is missing or required files are not present. 
    
    """
    home = home or Path.home()
    tar_in_bundle = bundle_root / "vscode-server" / commit / "server-linux-x64.tar.gz"
    if not tar_in_bundle.exists():
        raise RemoteServerError(f"Missing server tarball for commit {commit}: {tar_in_bundle}")

    target = home / ".vscode-server" / "bin" / commit
    target.mkdir(parents=True, exist_ok=True)

    # Extract server bundle
    with tarfile.open(tar_in_bundle, "r:gz") as t:
        t.extractall(target)

    # server.sh must exist; make it executable
    server_sh = target / "server.sh"
    if not server_sh.exists():
        raise RemoteServerError(f"server.sh not found under {target}")
    server_sh.chmod(0o755)

    return target

def validate_commit_tree(target: Path) -> None:
    """
    OPTIONAL
    Stronger validation to catch partial or corrupt installs
    Raises RemoteServerError listing missing files.
    """
    needed = [target / "server.sh", target / "node", target / "bin" / "code-server"]
    missing = [str(p) for p in needed if not p.exists()]
    if missing: 
        raise RemoteServerError(
            f"Incomplete VS Code server under {target}; missing: {', '.join(missing)}"
        )

# --- Helpers to prepare bundle root from the downloaded archive ZIP ---
from pathlib import Path
import zipfile

def prepare_bundle_root_from_zip(archive_zip: Path, commit: str, temp_dir: Path) -> Path:
    """
    Extract only the VS Code server tarball from the archive ZIP into a small on-disk
    'bundle root' so preseed_server(commit, bundle_root) can run without unzipping
    the entire archive.

    Accepts either of these in the ZIP:
      - bundle/vscode-server/<commit>/server-linux-x64.tar.gz
      - vscode-server/<commit>/server-linux-x64.tar.gz

    Returns:
      Path to the created bundle root directory: temp_dir / 'bundle'
    """
    bundle_root = temp_dir / "bundle"
    bundle_root.mkdir(parents=True, exist_ok=True)

    candidates = [
        f"bundle/vscode-server/{commit}/server-linux-x64.tar.gz",
        f"vscode-server/{commit}/server-linux-x64.tar.gz",
    ]

    try:
        with zipfile.ZipFile(archive_zip, "r") as zf:
            names = set(zf.namelist())
            found = next((m for m in candidates if m in names), None)
            if not found:
                raise RemoteServerError(
                    f"Archive {archive_zip} does not contain expected member: "
                    f"vscode-server/{commit}/server-linux-x64.tar.gz (with or without leading 'bundle/')"
                )

            # Normalize destination path to remove leading "bundle/" if present
            normalized = found[7:] if found.startswith("bundle/") else found  # strip "bundle/"
            dest = bundle_root / normalized
            dest.parent.mkdir(parents=True, exist_ok=True)

            with zf.open(found, "r") as src, open(dest, "wb") as out:
                out.write(src.read())

    except zipfile.BadZipFile as exc:
        raise RemoteServerError(f"Invalid ZIP: {archive_zip}") from exc

    return bundle_root
