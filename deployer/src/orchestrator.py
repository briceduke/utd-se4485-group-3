from __future__ import annotations
import json
from pathlib import Path

from .config_parser import parse_config, parse_cli_config, merge_configs
from .logger import get_logger, LogConfig
from .path_guard import ensure_paths
from .archive_downloader import fetch_archive_and_manifest
from .backup_cleanup import apply_replace_mode
from .expander_verifier import expand_and_verify, install_extensions
from .remote_server import preseed_server, validate_commit_tree, download_server_archive

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

    # --- Optional offline Remote-SSH preseed (automatic if server_archive_url is present) ---
    server_archive_url = config["source"].get("server_archive_url")
    if server_archive_url:
        # Read commit ID from manifest
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest_data = json.load(f)
            commit = manifest_data.get("vscode_commit_id")
            
            if not commit:
                logger.warning("server_archive_url is present but manifest does not contain vscode_commit_id; skipping preseed")
            else:
                try:
                    # Check if it's a URL or a local path
                    is_url = server_archive_url.startswith(("http://", "https://"))
                    if is_url:
                        # Treat as URL and download it
                        logger.info("Downloading server archive from %s", server_archive_url)
                        server_tarball_path = download_server_archive(
                            server_archive_url,
                            Path(config["plan"]["temp_dir"]),
                            config["source"]["retries"],
                            logger
                        )
                    else:
                        # Use local path directly
                        server_tarball_path = Path(server_archive_url)
                        if not server_tarball_path.exists():
                            logger.error("Server archive path does not exist: %s", server_tarball_path)
                            return 1
                        logger.info("Using local server archive at %s", server_tarball_path)
                    
                    target = preseed_server(commit, server_tarball_path)
                    validate_commit_tree(target)
                    logger.info("Pre-seeded VS Code server at %s", target)
                except Exception as e:
                    logger.error("Preseed failed for commit %s: %s", commit, e)
                    return 1
        except Exception as e:
            logger.error("Failed to read manifest to get commit ID: %s", e)
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

    # 8) Install extensions using VS Code server's code CLI
    # Get commit ID from manifest for locating the code CLI
    commit_id = None
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        commit_id = manifest_data.get("vscode_commit_id")
    except Exception as e:
        logger.debug(f"Could not read commit ID from manifest: {e}")
    
    install_extensions(
        manifest_path,
        config["deployment"]["target_dir"],
        commit_id,
        config["deployment"]["dry_run"],
        logger
    )

    return 0
