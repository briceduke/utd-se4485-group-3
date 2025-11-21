from .config_parser import parse_config, parse_cli_config, merge_configs
from .logger import get_logger, LogConfig
from .path_guard import ensure_paths
from .archive_downloader import fetch_archive_and_manifest
from .backup_cleanup import apply_replace_mode
from .expander_verifier import expand_and_verify

def run(config_path: str | None = None, **kwargs) -> int:
    """
    Main orchestrator function that coordinates the deployment process.

    Args:
        config_path: Path to the configuration YAML file, or None for default
        kwargs: Command line arguments

    Returns:
        Exit code: 0 for success, non-zero for failure

    The deployment process follows these steps:
    1. Parse configuration file
    2. Prioritize command line args over config file
    3. Set up logging based on config
    4. Download and fetch the extensions archive
    5. Apply replace mode (backup existing extensions if needed)
    6. Expand and verify the archive contents
    7. Deploy extensions to target directory
    8. Clean up temporary files and backup if successful
    """
    yaml_config = parse_config(config_path)

    cli_config = parse_cli_config(**kwargs)

    config = merge_configs(yaml_config, cli_config)

    path_result = ensure_paths(
        config.get("plan")["backup_dir"],
        config.get("plan")["temp_dir"],
        config.get("deployment")["target_dir"],
        config.get("logging")["file"]
    )

    logger = get_logger(LogConfig(
        name="deployer",
        level=config.get("logging")["level"],
        log_file=config.get("logging")["file"],
        to_console=config.get("logging").get("to_console", True),
        to_syslog=config.get("logging").get("to_syslog", False)
    ))

    archive_path, manifest_path = fetch_archive_and_manifest(
        config.get("source")["archive_url"],
        config.get("source")["manifest_url"],
        config.get("plan")["temp_dir"],
        config.get("source")["retries"],
        logger
    )

    apply_replace_mode(
        config.get("plan")["replace_mode"],
        config.get("plan")["backup_dir"],
        config.get("plan")["temp_dir"],
        config.get("plan")["include_extensions"],
        config.get("plan")["exclude_extensions"],
        config.get("deployment")["target_dir"],
        logger
    )

    expand_and_verify(
        archive_path,
        manifest_path,
        config.get("deployment")["target_dir"],
        config.get("deployment")["verify_integrity"],
        config.get("deployment")["dry_run"],
        logger
    )

    return 0
