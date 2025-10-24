import os
import logging
import requests
from pathlib import Path
from time import sleep

def download_extensions(extensions: list[dict], download_dir: str,
                       retries: int, skip_failed: bool) -> list[str]:
    """
    Downloads VSCode extensions from the Open VSX marketplace.

    Args:
        extensions: List of dicts with "name" (e.g., 'ms-python.python') and "version" ('latest' or specific version)
        download_dir: Directory path where downloaded files will be saved
        retries: Number of download retry attempts
        skip_failed: Whether to continue if a download fails

    Returns:
        List of local file paths for successfully downloaded extensions
    """
    os.makedirs(download_dir, exist_ok=True)
    logger = logging.getLogger("Downloader")
    logger.setLevel(logging.INFO)

    downloaded_files = []

    for ext in extensions:
        name = ext.get("name")
        version = ext.get("version", "latest")
        retry_count = 0
        success = False

        # Split into publisher + extension name
        try:
            publisher, ext_name = name.split(".")
        except ValueError:
            logger.error(f"Invalid extension name: {name}")
            if not skip_failed:
                raise
            continue

        # Build download URL (using Open VSX API)
        if version == "latest":
            url = f"https://open-vsx.org/api/{publisher}/{ext_name}/latest/file/{ext_name}.vsix"
        else:
            url = f"https://open-vsx.org/api/{publisher}/{ext_name}/{version}/file/{ext_name}-{version}.vsix"

        logger.info(f"Downloading {name}@{version}...")

        while retry_count < retries and not success:
            try:
                response = requests.get(url, stream=True, timeout=15)
                if response.status_code != 200:
                    raise Exception(f"Bad response: {response.status_code}")

                file_path = Path(download_dir) / f"{ext_name}-{version}.vsix"

                with open(file_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                logger.info(f"Downloaded {name} → {file_path}")
                downloaded_files.append(str(file_path))
                success = True

            except Exception as e:
                retry_count += 1
                logger.warning(f"Attempt {retry_count}/{retries} failed for {name}: {e}")
                if retry_count < retries:
                    sleep(2)  # wait a bit before retrying

        if not success:
            logger.error(f"Failed to download {name} after {retries} retries.")
            if not skip_failed:
                raise RuntimeError(f"Download failed: {name}")
            # skip if allowed
            continue

        # TODO: Verify integrity checksum (once Manifest Builder is ready)

    return downloaded_files