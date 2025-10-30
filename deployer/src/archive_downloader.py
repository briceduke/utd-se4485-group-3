import os
import time
import requests
from pathlib import Path
from urllib.parse import urljoin

def fetch_archive_and_manifest(archive_url: str, temp_dir: str, retries: int = 3) -> tuple[str, str]:
    """
    Fetch the extensions archive (.zip) and its manifest (.json) from the specified source URL.

    Args:
        archive_url: Base URL where the archive and manifest are hosted (e.g., 'https://server.com/releases/')
        temp_dir: Directory for storing downloaded files temporarily
        retries: Number of retry attempts for failed downloads

    Returns:
        (archive_path, manifest_path): Paths to the downloaded archive and manifest files

    Raises:
        Exception: If download fails after all retries
    """
    os.makedirs(temp_dir, exist_ok=True)
    archive_path = os.path.join(temp_dir, "extensions.zip")
    manifest_path = os.path.join(temp_dir, "manifest.json")

    def _download(url: str, dest: str):
        for attempt in range(1, retries + 1):
            try:
                print(f"[Downloader] Attempt {attempt}: Fetching {url}")
                response = requests.get(url, stream=True, timeout=10)
                response.raise_for_status()

                with open(dest, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                print(f"[Downloader] ✅ Successfully downloaded {os.path.basename(dest)}")
                return
            except Exception as e:
                print(f"[Downloader] ⚠ Error fetching {url}: {e}")
                if attempt < retries:
                    wait_time = 2 ** attempt
                    print(f"[Downloader] Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    raise Exception(f"Failed to download {url} after {retries} attempts.") from e

    # Construct file URLs (assuming both are in the same base directory)
    archive_file_url = urljoin(archive_url, "extensions.zip")
    manifest_file_url = urljoin(archive_url, "manifest.json")

    _download(archive_file_url, archive_path)
    _download(manifest_file_url, manifest_path)

    return archive_path, manifest_path
