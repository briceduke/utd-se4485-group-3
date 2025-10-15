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
    raise NotImplementedError
