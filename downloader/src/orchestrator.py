from .config_parser import parse_config, parse_cli_config, merge_configs
from .path_guard import ensure_paths
from .logger import get_logger, LogConfig
from .extension_repo import download_extensions, download_vscode_server
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

    path_result = ensure_paths(
        config.get("output")["directory"],       # cache_dir
        config.get("output")["directory"],       # output_zip - same as cache_dir; ZIP file is written to this directory
        config.get("logging")["file"]
    )

    logger = get_logger(LogConfig(
        name="downloader",
        level=config.get("logging")["level"],
        log_file=config.get("logging")["file"],
        to_console=config.get("logging").get("to_console", True),
        to_syslog=config.get("logging").get("to_syslog", False)
    ))

    extensions = download_extensions(config.get("extensions"),
                                     config.get("output")["directory"],
                                     config.get("download")["retries"],
                                     config.get("download")["skip_failed"],
                                     logger)

    # Download VS Code Server if commit_id is provided
    server_path = None
    commit_id = None
    if "vscode_version" in config and "commit_id" in config["vscode_version"]:
        commit_id = config["vscode_version"]["commit_id"]
        server_path = download_vscode_server(
            commit_id,
            config.get("output")["directory"],
            config.get("download")["retries"],
            logger
        )
        if server_path is None:
            logger.warning("VS Code Server download failed, but continuing with extensions")

    zip_path, manifest_path = build_zip_and_manifest(
        extensions,
        config.get("output")["directory"],
        config.get("output")["name_template"],
        config.get("extensions"),
        commit_id,
        server_path,
        logger
    )

    return 0
