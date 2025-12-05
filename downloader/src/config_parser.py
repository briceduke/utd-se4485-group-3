import yaml
import os

def parse_config(path: str | None) -> dict:
    """
    Parse the configuration YAML file and return a structured config dictionary.

    Args:
        path: Path to the YAML configuration file, or None for default

    Returns:
        Dictionary containing parsed configuration with the following structure:
        {
            'extensions': list[dict],  # [{'name': str, 'version': str}, ...]
            'vscode_version': {
                'commit_id': str  # VS Code commit ID for server download
            },
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
    
    Raises:
        ValueError: If configuration is invalid or missing required fields
    """
    default_path = os.path.join(os.getcwd(), 'downloader', 'examples', 'downloader.yaml')
    config_path = path or default_path

    try:
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file) or {}
    except Exception as e:
        raise ValueError(f"Failed to load config: {e}")

    required_sections = ['extensions', 'output', 'download', 'logging']
    missing = [s for s in required_sections if s not in data]
    if missing:
        raise ValueError(f"Missing sections: {', '.join(missing)}")
    
    # Validate vscode_version if present
    if 'vscode_version' in data:
        vscode_version = data['vscode_version']
        if not isinstance(vscode_version, dict):
            raise ValueError("'vscode_version' must be a dictionary")
        if 'commit_id' not in vscode_version:
            raise ValueError("Missing 'commit_id' in vscode_version")
        if not isinstance(vscode_version['commit_id'], str) or not vscode_version['commit_id']:
            raise ValueError("'commit_id' must be a non-empty string")

    extensions = data['extensions']
    if not isinstance(extensions, list):
        raise ValueError("'extensions' must be a list")
    for ext in extensions:
        if not isinstance(ext, dict):
            raise ValueError("Extension must be a dictionary")
        if 'name' not in ext:
            raise ValueError("Extension missing 'name'")
        ext['version'] = ext.get('version', 'latest')

    output = data['output']
    if 'directory' not in output:
        raise ValueError("Missing 'directory' in output")
    if 'name_template' not in output:
        raise ValueError("Missing 'name_template' in output")

    download = data['download']
    if 'retries' not in download:
        raise ValueError("Missing 'retries' in download")
    if not isinstance(download['retries'], int) or download['retries'] < 0:
        raise ValueError("'retries' must be a non-negative integer")
    
    if 'skip_failed' not in download:
        raise ValueError("Missing 'skip_failed' in download")
    if not isinstance(download['skip_failed'], bool):
        raise ValueError("'skip_failed' must be a boolean")

    logging = data['logging']
    logging['level'] = logging.get('level', 'INFO').upper()
    if logging['level'] not in ['DEBUG', 'INFO', 'WARNING', 'ERROR']:
        raise ValueError(f"Invalid log level: {logging['level']}")
    logging['file'] = logging.get('file')
    logging['to_console'] = logging.get('to_console', True) #default state is console logging
    logging['to_syslog'] = logging.get('to_syslog', False)

    return data

def _parse_extension_string(extension_str: str) -> dict:
    """
    Parse an extension string into a dict with 'name' and 'version' fields.
    
    Args:
        extension_str: Extension string in format "publisher.name" or "publisher.name@version"
    
    Returns:
        Dictionary with 'name' and 'version' fields
    """
    parts = extension_str.rsplit('@', 1)
    return {'name': parts[0], 'version': parts[1] if len(parts) > 1 else 'latest'}

def parse_cli_config(**kwargs) -> dict:
    """
    Parse the command line arguments and return a structured config dictionary.
    Only includes values that were actually provided (not None).

    Args:
        kwargs: Command line arguments

    Returns:
        Dictionary containing parsed configuration with the following structure:
        {
            'extensions': list[dict],  # [{'name': str, 'version': str}, ...]
            'exclude_extensions': list[dict],  # [{'name': str, 'version': str}, ...]
            'vscode_version': {
                'commit_id': str  # VS Code commit ID for server download
            },
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
    config = {}

    # Handle include_extensions - replaces base extensions list
    if (ie := kwargs.get("include_extensions")) is not None:
        config['extensions'] = [_parse_extension_string(ext) for ext in ie]
    
    # Handle exclude_extensions - filters out from base extensions list
    if (ee := kwargs.get("exclude_extensions")) is not None:
        config['exclude_extensions'] = [_parse_extension_string(ext) for ext in ee]

    output = {}
    if (od := kwargs.get("output_dir")) is not None:
        output['directory'] = od
    if (nt := kwargs.get("name_template")) is not None:
        output['name_template'] = nt
    if output:
        config['output'] = output

    download = {}
    if (rt := kwargs.get("retries")) is not None:
        download['retries'] = rt
    if (sf := kwargs.get("skip_failed")) is not None:
        download['skip_failed'] = sf
    if download:
        config['download'] = download

    logging = {}
    if (ll := kwargs.get("log_level")) is not None:
        logging['level'] = ll.upper()
    if (lf := kwargs.get("log_file")) is not None:
        logging['file'] = lf
    if logging:
        config['logging'] = logging

    # Handle vscode_version
    if (commit_id := kwargs.get("vscode_commit_id")) is not None:
        config['vscode_version'] = {'commit_id': commit_id}

    return config

def merge_configs(yaml_config: dict, cli_config: dict) -> dict:
    """
    Merge CLI configuration into YAML configuration, with CLI values taking precedence.
    For extensions, CLI include_extensions replaces the YAML extensions list.
    CLI exclude_extensions filters out extensions from the final list.
    
    Args:
        yaml_config: Configuration from YAML file
        cli_config: Configuration from CLI arguments
    
    Returns:
        Merged configuration dictionary
    """
    merged = yaml_config.copy()
    
    # Handle extensions specially - if CLI has extensions, replace YAML extensions
    if 'extensions' in cli_config:
        merged['extensions'] = cli_config['extensions'].copy()
    
    # Apply exclude_extensions if present (works on either YAML or CLI extensions)
    if 'exclude_extensions' in cli_config:
        excluded_names = {ext['name'] for ext in cli_config['exclude_extensions']}
        merged['extensions'] = [
            ext for ext in merged.get('extensions', [])
            if ext['name'] not in excluded_names
        ]
    
    # Merge other sections
    for section, values in cli_config.items():
        if section in ['extensions', 'exclude_extensions']:
            continue  # Already handled above
        merged.setdefault(section, {}).update(values)
    
    return merged
