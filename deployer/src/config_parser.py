def parse_config(path: str | None) -> dict:
    """
    Parse the configuration YAML file and return a structured config dictionary.

    Args:
        path: Path to the YAML configuration file, or None for default

    Returns:
        Dictionary containing parsed configuration with the following structure:
        {
            'plan': {
                'replace_mode': str,  # 'none', 'prune', or 'nuke'
                'backup_dir': str,
                'temp_dir': str,
                'include_extensions': list[dict],  # [{'name': str, 'version': str}, ...]
                'exclude_extensions': list[dict]   # [{'name': str, 'version': str}, ...]
            },
            'source': {
                'archive_url': str,
                'retries': int
            },
            'deployment': {
                'target_dir': str,
                'verify_integrity': str,  # 'error', 'none', or 'warn'
                'dry_run': bool
            },
            'logging': {
                'level': str,  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                'file': str | None
            }
        }
    """
    raise NotImplementedError
