import yaml
import validators
import os

def parse_config(path: str | None) -> dict:
    """
    Parse the configuration YAML file and return a structured config dictionary.

    Args:
        path: Path to the YAML configuration file, or None for default

    Returns:
        Dictionary containing parsed configuration with the following structure:
        {
            'plan': {
                'replace_mode': str,  # 'NONE', 'REPLACE', or 'CLEAN'
                'backup_dir': str,
                'temp_dir': str,
                'include_extensions': list[dict],  # [{'name': str, 'version': str}, ...]
                'exclude_extensions': list[dict]   # [{'name': str, 'version': str}, ...]
            },
            'source': {
                'archive_url': str,
                'manifest_url': str,
                'retries': int
            },
            'deployment': {
                'target_dir': str,
                'verify_integrity': str,  # 'NONE', 'WARN', or 'ERROR'
                'dry_run': bool
            },
            'logging': {
                'level': str,  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                'file': str | None
            }
        }
    
    Raises:
        ValueError: If configuration is invalid or missing required fields
    """
    default_path = os.path.join(os.getcwd(), 'deployer', 'examples', 'test-deployer.yaml')
    config_path = path or default_path

    try:
        with open(config_path, 'r') as file:
            data = yaml.safe_load(file) or {}
    except Exception as e:
        raise ValueError(f"Failed to load config: {e}")

    required_sections = ['plan', 'source', 'deployment', 'logging']
    missing = [s for s in required_sections if s not in data]
    if missing:
        raise ValueError(f"Missing sections: {', '.join(missing)}")

    plan = data['plan']
    if 'replace_mode' not in plan:
        raise ValueError("Missing 'replace_mode' in plan")
    plan['replace_mode'] = plan['replace_mode'].upper()
    if plan['replace_mode'] not in ['NONE', 'REPLACE', 'CLEAN']:
        raise ValueError(f"Invalid replace_mode: {plan['replace_mode']}")

    if 'backup_dir' not in plan:
        raise ValueError("Missing 'backup_dir' in plan")
    if 'temp_dir' not in plan:
        raise ValueError("Missing 'temp_dir' in plan")

    plan['include_extensions'] = plan.get('include_extensions', [])
    for ext in plan['include_extensions']:
        if 'name' not in ext:
            raise ValueError("Extension in include_extensions missing 'name'")
        ext['version'] = ext.get('version', 'latest')

    plan['exclude_extensions'] = plan.get('exclude_extensions', [])
    for ext in plan['exclude_extensions']:
        if 'name' not in ext:
            raise ValueError("Extension in exclude_extensions missing 'name'")
        ext['version'] = ext.get('version', 'latest')

    source = data['source']
    if 'archive_url' not in source:
        raise ValueError("Missing 'archive_url' in source")
    # if not validators.url(source['archive_url']):
    #     raise ValueError(f"Invalid archive_url: {source['archive_url']}")

    if 'manifest_url' not in source:
        raise ValueError("Missing 'manifest_url' in source")
    # if not validators.url(source['manifest_url']):
    #     raise ValueError(f"Invalid manifest_url: {source['manifest_url']}")

    source['retries'] = source.get('retries', 3)

    deployment = data['deployment']
    if 'target_dir' not in deployment:
        raise ValueError("Missing 'target_dir' in deployment")

    if 'verify_integrity' not in deployment:
        raise ValueError("Missing 'verify_integrity' in deployment")
    deployment['verify_integrity'] = deployment['verify_integrity'].upper()
    if deployment['verify_integrity'] not in ['NONE', 'WARN', 'ERROR']:
        raise ValueError(f"Invalid verify_integrity: {deployment['verify_integrity']}")

    deployment['dry_run'] = deployment.get('dry_run', False)

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
            'plan': {
                'replace_mode': str,  # 'NONE', 'REPLACE', or 'CLEAN'
                'backup_dir': str,
                'temp_dir': str,
                'include_extensions': list[dict],  # [{'name': str, 'version': str}, ...]
                'exclude_extensions': list[dict]   # [{'name': str, 'version': str}, ...]
            },
            'source': {
                'archive_url': str,
                'manifest_url': str,
                'retries': int
            },
            'deployment': {
                'target_dir': str,
                'verify_integrity': str,  # 'NONE', 'WARN', or 'ERROR'
                'dry_run': bool
            },
            'logging': {
                'level': str,  # 'DEBUG', 'INFO', 'WARNING', 'ERROR'
                'file': str | None
            }
        }
    """
    config = {}

    plan = {}
    if (rm := kwargs.get("replace_mode")) is not None:
        plan['replace_mode'] = rm.upper()
    if (bd := kwargs.get("backup_dir")) is not None:
        plan['backup_dir'] = bd
    if (td := kwargs.get("temp_dir")) is not None:
        plan['temp_dir'] = td
    if (ie := kwargs.get("include_extensions")) is not None:
        plan['include_extensions'] = [_parse_extension_string(ext) for ext in ie]
    if (ee := kwargs.get("exclude_extensions")) is not None:
        plan['exclude_extensions'] = [_parse_extension_string(ext) for ext in ee]
    if plan:
        config['plan'] = plan

    source = {}
    if (au := kwargs.get("archive_url")) is not None:
        source['archive_url'] = au
    if (mu := kwargs.get("manifest_url")) is not None:
        source['manifest_url'] = mu
    if (rt := kwargs.get("retries")) is not None:
        source['retries'] = rt
    if source:
        config['source'] = source

    deployment = {}
    if (tg := kwargs.get("target_dir")) is not None:
        deployment['target_dir'] = tg
    if (vi := kwargs.get("verify_integrity")) is not None:
        deployment['verify_integrity'] = vi.upper()
    if (dr := kwargs.get("dry_run")) is not None:
        deployment['dry_run'] = dr
    if deployment:
        config['deployment'] = deployment

    logging = {}
    if (ll := kwargs.get("log_level")) is not None:
        logging['level'] = ll.upper()
    if (lf := kwargs.get("log_file")) is not None:
        logging['file'] = lf
    if logging:
        config['logging'] = logging

    return config

def merge_configs(yaml_config: dict, cli_config: dict) -> dict:
    """
    Merge CLI configuration into YAML configuration, with CLI values taking precedence.
    
    Args:
        yaml_config: Configuration from YAML file
        cli_config: Configuration from CLI arguments
    
    Returns:
        Merged configuration dictionary
    """
    merged = yaml_config.copy()
    for section, values in cli_config.items():
        merged.setdefault(section, {}).update(values)
    return merged