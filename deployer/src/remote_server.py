from __future__ import annotations
import tarfile, zipfile, os, stat, time, requests, shutil
from pathlib import Path
from logging import Logger

class RemoteServerError(RuntimeError):
    pass

def preseed_server(commit: str, server_tarball_path: Path, home: Path | None = None) -> Path:
    """
    Unpack the VS Code server tarball into ~/.vscode-server/bin/<commit> and ensure key files are executable.
    
    Args:
        commit: VS Code commit hash
        server_tarball_path: Path to the server tarball (vscode-server-linux-x64.tar.gz)
        home: Home directory (defaults to Path.home())
    
    Returns:
        Path to the extracted server directory
    """
    home = home or Path.home()
    if not server_tarball_path.exists():
        raise RemoteServerError(f"Missing server tarball: {server_tarball_path}")

    target = home / ".vscode-server" / "bin" / commit
    success_marker = target / "0"
    
    # Short-circuit: If the success marker already exists, server is already installed
    if success_marker.exists():
        return target
    
    # Corruption cleanup: If directory exists but marker is missing, assume corruption and clean up
    if target.exists() and not success_marker.exists():
        shutil.rmtree(target)
    
    target.mkdir(parents=True, exist_ok=True)

    # Extract server bundle, stripping the top-level directory (vscode-server-linux-x64/)
    # The official tarball wraps everything in vscode-server-linux-x64/, but VS Code expects
    # files directly in ~/.vscode-server/bin/<commit>/
    with tarfile.open(server_tarball_path, "r:gz") as t:
        # Get all members and strip the top-level directory
        members = t.getmembers()
        prefix = "vscode-server-linux-x64"
        
        for member in members:
            original_name = member.name
            # Skip the root directory entry itself
            if member.isdir() and original_name == prefix:
                continue
            
            # Strip the prefix from the path
            if original_name.startswith(prefix + "/"):
                # Modify the member's name to remove the prefix
                member.name = original_name[len(prefix + "/"):]
                t.extract(member, target)
            elif original_name == prefix:
                # Skip the root directory
                continue
            else:
                # Fallback: if no prefix found, extract as-is
                # (shouldn't happen with official tarballs, but handle gracefully)
                t.extract(member, target)

    # Ensure expected files exist and are executable
    # Note: server.sh may not exist in newer VS Code server versions, but bin/code-server should
    required_files = []
    if (target / "server.sh").exists():
        required_files.append("server.sh")
    required_files.extend(["node", "bin/code-server"])
    
    for rel in required_files:
        p = target / rel
        if not p.exists():
            raise RemoteServerError(f"Missing required server file: {p}")
        _make_executable(p)

    # Create success marker file (0-byte file named "0")
    # VS Code Remote-SSH looks for this to confirm installation is complete
    success_marker.touch()
    
    # Set the modification time to be newer than the executable files
    # This ensures VS Code recognizes the installation as complete
    current_time = time.time()
    os.utime(success_marker, (current_time, current_time))

    return target

def validate_commit_tree(target: Path) -> None:
    """Validate that node and bin/code-server exist and are executable. server.sh is optional."""
    required_files = []
    if (target / "server.sh").exists():
        required_files.append("server.sh")
    required_files.extend(["node", "bin/code-server"])
    
    for rel in required_files:
        p = target / rel
        if not p.exists():
            raise RemoteServerError(f"Expected file missing after extract: {p}")
        if not os.access(p, os.X_OK):
            raise RemoteServerError(f"Expected file not executable: {p}")

def _make_executable(p: Path) -> None:
    mode = p.stat().st_mode
    p.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

def download_server_archive(server_archive_url: str, temp_dir: Path, retries: int, logger: Logger | None = None) -> Path:
    """
    Download the server archive from the given URL to the temp directory.
    
    Args:
        server_archive_url: URL to download the server archive from
        temp_dir: Temporary directory to download to
        retries: Number of retry attempts
        logger: Logger instance
    
    Returns:
        Path to the downloaded server archive file
    """
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()
    
    temp_dir.mkdir(parents=True, exist_ok=True)
    server_archive_path = temp_dir / "vscode-server-linux-x64.tar.gz"
    
    for attempt in range(1, retries + 1):
        try:
            logger.info(f"Attempt {attempt}: Fetching server archive from {server_archive_url}")
            response = requests.get(server_archive_url, stream=True, timeout=10)
            response.raise_for_status()
            
            with open(server_archive_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logger.info(f"Successfully downloaded server archive to {server_archive_path}")
            return server_archive_path
        except Exception as e:
            logger.warning(f"Error fetching server archive: {e}")
            if attempt < retries:
                wait_time = 2 ** attempt
                logger.debug(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed to download server archive after {retries} attempts.")
                raise RemoteServerError(f"Failed to download server archive after {retries} attempts.") from e
