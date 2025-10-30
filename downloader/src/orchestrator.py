from .config_parser import parse_config, parse_cli_config, merge_configs
from .path_guard import ensure_paths
from .logger import get_logger
from .extension_repo import download_extensions
from .packaging import build_zip_and_manifest

def run(config_path: str | None = None, **kwargs) -> int:
    """
    Main orchestrator function that coordinates the download process.

    Args:
        config_path: Path to the configuration YAML file, or None for default
        kwargs: Command line arguments

    Returns:
        Exit code: 0 for success, non-zero for failure

    The download process follows these steps:
    1. Parse configuration file
    2. Prioritize command line args over config file
    3. Set up logging based on config
    4. Download specified extensions from marketplace
    5. Package downloaded extensions into ZIP archive
    6. Generate manifest file with extension details
    7. Save output to specified directory with naming template
    """
    yaml_config = parse_config(config_path)

    cli_config = parse_cli_config(**kwargs)

    config = merge_configs(yaml_config, cli_config)

    logger = get_logger(config.get("logging")["level"])

    ensure_paths([
        config.get("output")["directory"],
        config.get("logging")["file"]
    ])

    print(config)
    
    extensions = download_extensions(config.get("extensions"),
                                     config.get("output")["directory"],
                                     config.get("download")["retries"],
                                     config.get("download")["skip_failed"])

    zip_path, manifest_path = build_zip_and_manifest(extensions,
                                                     config.get("output")["directory"],
                                                    config.get("output")["name_template"])

    return 0
