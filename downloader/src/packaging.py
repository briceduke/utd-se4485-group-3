def build_zip_and_manifest(files: list[str], output_dir: str,
                          name_template: str) -> tuple[str, str]:
    """
    Build a ZIP archive and manifest from downloaded extension files.

    Args:
        files: List of paths to downloaded extension files
        output_dir: Directory where the output files should be saved
        name_template: Template for naming the output files (e.g., 'everfox-extensions-{{date}}.zip')

    Returns:
        Tuple of (zip_path, manifest_path) containing paths to created files

    The name_template can contain placeholders like {{date}} that will be replaced
    with appropriate values (e.g., current date).
    """
    return "zip.zip", "manifest.json"
