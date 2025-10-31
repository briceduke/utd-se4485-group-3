import os
import logging
import requests
from pathlib import Path
from time import sleep


def get_vscode_vsix_url(ext_name: str, version: str = "latest") -> str:
    """
    Queries Microsoft's VS Code Marketplace for the given extension and returns
    the direct .vsix download URL.
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
                    return f"{v['assetUri']}/Microsoft.VisualStudio.Services.VSIXPackage"

        # Default: use latest available version
        asset_uri = extension["versions"][0]["assetUri"]
        return f"{asset_uri}/Microsoft.VisualStudio.Services.VSIXPackage"

    except (KeyError, IndexError):
        raise ValueError(f"Extension not found or invalid: {ext_name}")


def download_extensions(extensions: list[dict], download_dir: str,
                        retries: int = 3, skip_failed: bool = True) -> list[str]:
    """
    Downloads VSCode extensions (.vsix) from Microsoft's official Marketplace.

    Args:
        extensions: List of dicts with "name" (e.g., 'ms-python.python') and
                    "version" ('latest' or specific version)
        download_dir: Directory where downloaded files will be saved
        retries: Number of download retry attempts
        skip_failed: Whether to continue if a download fails

    Returns:
        List of local file paths for downloaded extensions (even if they failed to download)
    """
    os.makedirs(download_dir, exist_ok=True)
    logger = logging.getLogger("Downloader")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

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
            url = get_vscode_vsix_url(name, version)
        except Exception as e:
            logger.error(f"Failed to resolve {name}: {e}")
            if not skip_failed:
                raise
            continue

        logger.info(f"Downloading {name}@{version}")

        while retry_count < retries and not success:
            try:
                response = requests.get(url, stream=True, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"Bad response: {response.status_code}")

                # Resolve filename from version (auto if latest)
                file_version = version
                if version == "latest":
                    # Extract actual version number from metadata if available
                    try:
                        metadata = requests.head(url).headers.get("Content-Disposition", "")
                        if "filename=" in metadata:
                            file_version = metadata.split("filename=")[-1].split(".vsix")[0].split("-")[-1]
                    except Exception:
                        pass

                file_path = Path(download_dir) / f"{ext_name}-{file_version}.vsix"

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