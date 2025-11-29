from __future__ import annotations
from pathlib import Path

from .config_parser import parse_config, parse_cli_config, merge_configs
from .logger import get_logger, LogConfig
from .path_guard import ensure_paths
from .archive_downloader import fetch_archive_and_manifest
from .backup_cleanup import apply_replace_mode
from .expander_verifier import expand_and_verify
from .remote_server import preseed_server, validate_commit_tree, prepare_bundle_root_from_zip

def run(config_path: str | None = None, **kwargs) -> int:
    """
    Main orchestrator function that coordinates the deployment process.
    """
    # 1-3) Parse + merge configs
    yaml_config = parse_config(config_path)
    cli_config = parse_cli_config(**kwargs)
    config = merge_configs(yaml_config, cli_config)

    # Ensure required paths exist and are writable (uses Max's PathGuard)
    ensure_paths(
        config["plan"]["backup_dir"],
        config["plan"]["temp_dir"],
        config["deployment"]["target_dir"],
        config["logging"]["file"]
    )

    # Logger (uses Max's logger)
    logger = get_logger(LogConfig(
        name="deployer",
        level=config["logging"]["level"],
        log_file=config["logging"]["file"],
        to_console=config["logging"].get("to_console", True),
        to_syslog=config["logging"].get("to_syslog", False)
    ))

    # 4) Fetch archive + manifest to temp dir
    archive_path, manifest_path = fetch_archive_and_manifest(
        config["source"]["archive_url"],
        config["source"]["manifest_url"],
        config["plan"]["temp_dir"],
        config["source"]["retries"],
        logger
    )

    # --- Optional offline Remote-SSH preseed (gated by commit) ---
    preseed = bool(kwargs.get("preseed_server"))
    commit = kwargs.get("vscode_commit")
    if preseed:
        if not commit:
            logger.warning("Preseed requested but --vscode-commit missing; skipping preseed")
        else:
            try:
                work = Path(config["plan"]["temp_dir"]) / "preseed_work"
                bundle_root = prepare_bundle_root_from_zip(Path(archive_path), commit, work)
                target = preseed_server(commit, bundle_root)
                validate_commit_tree(target)
                logger.info("Pre-seeded VS Code server at %s", target)
            except Exception as e:
                logger.error("Preseed failed for commit %s: %s", commit, e)
                return 1
    # -------------------------------------------------------------

    # 5) Apply replace/backup strategy
    apply_replace_mode(
        config["plan"]["replace_mode"],
        config["plan"]["backup_dir"],
        config["plan"]["temp_dir"],
        config["plan"]["include_extensions"],
        config["plan"]["exclude_extensions"],
        config["deployment"]["target_dir"],
        logger
    )

    # 6-7) Expand & verify (extensions)
    expand_and_verify(
        archive_path,
        manifest_path,
        config["deployment"]["target_dir"],
        config["deployment"]["verify_integrity"],
        config["deployment"]["dry_run"],
        logger
    )

    return 0
