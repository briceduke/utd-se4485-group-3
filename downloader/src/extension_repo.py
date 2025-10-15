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
    raise NotImplementedError
