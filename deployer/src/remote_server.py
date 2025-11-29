from __future__ import annotations
import tarfile, zipfile, os, stat
from pathlib import Path

class RemoteServerError(RuntimeError):
    pass

def preseed_server(commit: str, bundle_root: Path, home: Path | None = None) -> Path:
    """
    Unpack the VS Code server tarball into ~/.vscode-server/bin/<commit> and ensure key files are executable.
    bundle_root is expected to contain: vscode-server/<commit>/server-linux-x64.tar.gz
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

    # Ensure expected files exist and are executable
    for rel in ("server.sh", "node", "bin/code-server"):
        p = target / rel
        if not p.exists():
            raise RemoteServerError(f"Missing required server file: {p}")
        _make_executable(p)

    return target

def validate_commit_tree(target: Path) -> None:
    """Validate that server.sh, node, and bin/code-server exist and are executable."""
    for rel in ("server.sh", "node", "bin/code-server"):
        p = target / rel
        if not p.exists():
            raise RemoteServerError(f"Expected file missing after extract: {p}")
        if not os.access(p, os.X_OK):
            raise RemoteServerError(f"Expected file not executable: {p}")

def _make_executable(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def prepare_bundle_root_from_zip(zip_path: Path, commit: str, outdir: Path) -> Path:
    """
    Extract only the server tarball for the given commit from the downloader ZIP into:
        outdir/vscode-server/<commit>/server-linux-x64.tar.gz
    The ZIP may have a leading 'bundle/' prefix; we handle both.
    """
    outdir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        # find member that ends with /vscode-server/<commit>/server-linux-x64.tar.gz
        wanted_tail = f"vscode-server/{commit}/server-linux-x64.tar.gz"
        member_name = None
        for name in zf.namelist():
            if name.endswith(wanted_tail):
                member_name = name
                break
        if not member_name:
            raise RemoteServerError(
                f"Archive {zip_path} does not contain expected member: {wanted_tail}"
            )

        dest_dir = outdir / "vscode-server" / commit
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_file = dest_dir / "server-linux-x64.tar.gz"

        with zf.open(member_name, "r") as src, open(dest_file, "wb") as dst:
            dst.write(src.read())

    return outdir
