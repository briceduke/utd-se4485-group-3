import os
import logging
import requests
from pathlib import Path
from time import sleep

def download_extensions(extensions: list[dict], download_dir: str,
                       retries: int, skip_failed: bool) -> list[str]:
    """
    Download VSCode extensions from the marketplace.

    Args:
        extensions: List of extension specifications, each containing:
            {'name': str, 'version': str}
        download_dir: Directory to store downloaded extensions
        retries: Number of retry attempts for failed downloads
        skip_failed: Whether to skip failed downloads and continue

    Returns:
        List of paths to successfully downloaded extension files

    Each extension in the list should have:
    - name: The extension identifier (e.g., 'ms-python.python')
    - version: The version to download, or 'latest' for latest version
    """
    os.makedirs(download_dir, exist_ok=True)
    logger = logging.getLogger("Downloader")
    logger.setLevel(logging.INFO)

    downloaded = []

    for ext in extensions:
        name = ext.get("name")
        version = ext.get("version", "latest")
        success = False
        attempt = 0

        # Construct URL for Open VSX (open source VSCode marketplace)
        try:
            publisher, ext_name = name.split(".")
        except ValueError:
            logger.error(f"Invalid extension name format: {name}")
            if not skip_failed:
                raise
            continue

        if version == "latest":
            url = f"https://open-vsx.org/api/{publisher}/{ext_name}/latest/file/{ext_name}.vsix"
        else:
            url = f"https://open-vsx.org/api/{publisher}/{ext_name}/{version}/file/{ext_name}-{version}.vsix"

        logger.info(f"Downloading {name}@{version} from {url}")

        while attempt < retries and not success:
            attempt += 1
            try:
                response = requests.get(url, stream=True, timeout=20)
                if response.status_code != 200:
                    raise Exception(f"HTTP {response.status_code}")

                filepath = Path(download_dir) / f"{ext_name}-{version}.vsix"
                with open(filepath, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                downloaded.append(str(filepath))
                logger.info(f"✅ Downloaded {name} to {filepath}")
                success = True

            except Exception as e:
                logger.warning(f"⚠️ Attempt {attempt}/{retries} failed for {name}: {e}")
                if attempt < retries:
                    sleep(2)

        if not success:
            logger.error(f"❌ Failed to download {name} after {retries} retries.")
            if not skip_failed:
                raise RuntimeError(f"Failed to download {name}")
            # skip if allowed
            continue

    return downloaded