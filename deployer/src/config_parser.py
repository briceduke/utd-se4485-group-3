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
    return {
        'plan': {
            'replace_mode': 'none',
            'backup_dir': './backup',
            'temp_dir': './temp',
            'include_extensions': [],
            'exclude_extensions': [],
        },
        'source': {
            'archive_url': None,
            'retries': 3,
        },
        'deployment': {
            'target_dir': None,
            'verify_integrity': 'error',
            'dry_run': False,
        },
        'logging': {
            'level': 'INFO',
            'file': None,
        },
    }

def parse_cli_config(**kwargs) -> dict:
    """
    Parse the command line arguments and return a structured config dictionary.

    Args:
        kwargs: Command line arguments

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
    return {
        'plan': {
            'replace_mode': kwargs.get("replace_mode"),
            'backup_dir': kwargs.get("backup_dir"),
            'temp_dir': kwargs.get("temp_dir"),
            'include_extensions': [],
            'exclude_extensions': [],
        },
        'source': {
            'archive_url': kwargs.get("archive_url"),
            'retries': 3,
        },
        'deployment': {
            'target_dir': kwargs.get("target_dir"),
            'verify_integrity': kwargs.get("verify_integrity"),
            'dry_run': False,
        },
        'logging': {
            'level': kwargs.get("log_level"),
            'file': kwargs.get("log_file"),
        },
    }