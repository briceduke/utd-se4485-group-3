import os
import requests
from pathlib import Path
from time import sleep
from logging import Logger


def get_vscode_vsix_url(ext_name: str, version: str = "latest") -> tuple[str, str]:
    """
    Queries Microsoft's VS Code Marketplace for the given extension and returns
    the direct .vsix download URL and the resolved version.
    """
    publisher, name = ext_name.split(".")
    url = "https://marketplace.visualstudio.com/_apis/public/gallery/extensionquery"
    headers = {
        "Accept": "application/json;api-version=3.0-preview.1",
        "Content-Type": "application/json",
    }
    payload = {
        "filters": [{"criteria": [{"filterType": 7, "value": ext_name}]}],
        "flags": 103
    }

    res = requests.post(url, headers=headers, json=payload, timeout=15)
    res.raise_for_status()
    data = res.json()

    try:
        extension = data["results"][0]["extensions"][0]
        versions = extension.get("versions", [])
        if version != "latest":
            for v in versions:
                if v.get("version") == version:
                    return (f"{v['assetUri']}/Microsoft.VisualStudio.Services.VSIXPackage", version)

        # Default: use latest available version
        latest_version = extension["versions"][0]
        asset_uri = latest_version["assetUri"]
        return (f"{asset_uri}/Microsoft.VisualStudio.Services.VSIXPackage", latest_version["version"])

    except (KeyError, IndexError):
        raise ValueError(f"Extension not found or invalid: {ext_name}")


def download_extensions(extensions: list[dict], download_dir: str,
                        retries: int = 3, skip_failed: bool = True, logger: Logger | None = None) -> list[str]:
    """
    Downloads VSCode extensions (.vsix) from Microsoft's official Marketplace.

    Args:
        extensions: List of dicts with "name" (e.g., 'ms-python.python') and
                    "version" ('latest' or specific version)
        download_dir: Directory where downloaded files will be saved
        retries: Number of download retry attempts
        skip_failed: Whether to continue if a download fails
        logger: Logger instance (if None, logging is disabled)

    Returns:
        List of local file paths for downloaded extensions (even if they failed to download)
    """
    os.makedirs(download_dir, exist_ok=True)
    
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()

    downloaded_files = []

    for ext in extensions:
        name = ext.get("name")
        version = ext.get("version", "latest")
        retry_count = 0
        success = False

        try:
            publisher, ext_name = name.split(".")
        except ValueError:
            logger.error(f"Invalid extension name format: {name}")
            if not skip_failed:
                raise
            continue

        logger.info(f"Fetching VSIX URL for {name}@{version}...")
        try:
            url, resolved_version = get_vscode_vsix_url(name, version)
        except Exception as e:
            logger.error(f"Failed to resolve {name}: {e}")
            if not skip_failed:
                raise
            continue

        logger.info(f"Downloading {name}@{resolved_version}")

        while retry_count < retries and not success:
            try:
                response = requests.get(url, stream=True, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"Bad response: {response.status_code}")

                file_path = Path(download_dir) / f"{ext_name}-{resolved_version}.vsix"

                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                logger.info(f"✅ Downloaded {name} → {file_path}")
                downloaded_files.append(str(file_path))
                success = True

            except Exception as e:
                retry_count += 1
                logger.warning(f"Attempt {retry_count}/{retries} failed for {name}: {e}")
                if retry_count < retries:
                    sleep(2)

        if not success:
            logger.error(f"❌ Failed to download {name} after {retries} retries.")
            if not skip_failed:
                raise RuntimeError(f"Download failed: {name}")

    return downloaded_files


def download_vscode_server(commit_id: str, output_dir: str, retries: int = 3,
                          logger: Logger | None = None) -> str | None:
    """
    Downloads the VS Code Server binary for a specific commit ID.

    Args:
        commit_id: The VS Code commit ID
        output_dir: Directory where the server tarball will be saved
        retries: Number of download retry attempts
        logger: Logger instance (if None, logging is disabled)

    Returns:
        Path to the downloaded server tarball, or None if download failed
    """
    os.makedirs(output_dir, exist_ok=True)
    
    if logger is None:
        class NullLogger:
            def debug(self, *args, **kwargs): pass
            def info(self, *args, **kwargs): pass
            def warning(self, *args, **kwargs): pass
            def error(self, *args, **kwargs): pass
        logger = NullLogger()

    url = f"https://update.code.visualstudio.com/commit:{commit_id}/server-linux-x64/stable"
    output_path = Path(output_dir) / f"vscode-server-{commit_id}.tar.gz"

    logger.info(f"Downloading VS Code Server for commit {commit_id}...")
    logger.debug(f"Server URL: {url}")

    retry_count = 0
    success = False

    while retry_count < retries and not success:
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()

            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)

            logger.info(f"✅ Downloaded VS Code Server → {output_path}")
            success = True

        except Exception as e:
            retry_count += 1
            logger.warning(f"Attempt {retry_count}/{retries} failed for VS Code Server: {e}")
            if retry_count < retries:
                sleep(2)

    if not success:
        logger.error(f"❌ Failed to download VS Code Server after {retries} retries.")
        return None

    return str(output_path)