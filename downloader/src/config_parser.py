def parse_config(path: str | None) -> dict:
    """
    Parse the configuration YAML file and return a structured config dictionary.

    Args:
        path: Path to the YAML configuration file, or None for default

    Returns:
        Dictionary containing parsed configuration with the following structure:
        {
            'extensions': list[dict],  # [{'name': str, 'version': str}, ...]
            'output': {
                'directory': str,
                'name_template': str
            },
            'download': {
                'retries': int,
                'skip_failed': bool
            },
            'logging': {
                'level': str,  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                'file': str | None
            }
        }
    """
    return {
        'extensions': [],
        'output': {
            'directory': './downloads',
            'name_template': 'everfox-extensions-{{date}}.zip',
        },
        'download': {
            'retries': 3,
            'skip_failed': False,
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
        Dictionary containing parsed command line arguments with the following structure:
        {
            'extensions': list[dict],  # [{'name': str, 'version': str}, ...]
            'output': {
                'directory': str,
                'name_template': str
            },
            'download': {
                'retries': int,
                'skip_failed': bool
            },
            'logging': {
                'level': str,  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                'file': str | None
            }
        }
    """
    return {
        'extensions': [],
        'output': {
            'directory': kwargs.get("output_dir"),
            'name_template': kwargs.get("name_template"),
        },
        'download': {
            'retries': 3,
            'skip_failed': False,
        },
        'logging': {
            'level': kwargs.get("log_level"),
            'file': kwargs.get("log_file"),
        },
    }