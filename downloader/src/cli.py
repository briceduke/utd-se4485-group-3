import argparse
import os
from . import orchestrator

def _parse_bool(value: str) -> bool:
    """
    Parse a string value into a boolean.
    Accepts: true, false, yes, no, 1, 0 (case-insensitive)
    """
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        value_lower = value.lower()
        if value_lower in ('true', 'yes', '1', 'on'):
            return True
        if value_lower in ('false', 'no', '0', 'off'):
            return False
    raise argparse.ArgumentTypeError(f"Invalid boolean value: {value}")

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="everfox-downloader",
        description=(
            "This is the download-packager half (step 1) of a two-part application for collecting and distributing "
            "VSCode extensions across an airgapped environment. This will collect extensions from the VSCode "
            "marketplace and package them for distribution, producing both an archive of the extension files and a "
            "manifest of which extensions are included in the archive."
        ),
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument(
        "--config", type=str, default=None,
        metavar="FILE",
        help=(
            "Loads a configuration file. Overlapping values in the specified configuration will override those in the "
            "default or system configuration (for primitive values) or merge with values in the default or system "
            "configuration (for array and map values)."
        ))
    parser.add_argument(
        "--include-extensions", type=str, nargs="+", default=None, metavar="EXTENSION",
        help=(
            "Includes extensions to be added to the archive.\n"
            "Extra extensions are only included as long as this flag is supplied; this is not written to a "
            "configuration file.\n\n"
            "Extensions should use one of the formats:\n"
            "    publisher.name\n"
            "    publisher.name@version\n"
            "For example:\n"
            "    ms-python.python\n"
            "    redhat.vscode-yaml@1.19.1"
        ))
    parser.add_argument(
        "--exclude-extensions", type=str, nargs="+", default=None, metavar="EXTENSION",
        help=(
            "Excludes configured extensions from being added to the archive.\n"
            "Extensions are only excluded as long as this flag is supplied; this is not written to a "
            "configuration file.\n"
            "Format matches that of --include-extensions."
        ))
    parser.add_argument(
        "--output-dir", type=str, default=None,
        help="Sets the parent directory the extension archive and manifest will be written to.")
    parser.add_argument(
        "--name-template", type=str, default=None,
        help="Sets the format string template used to name the extension archive and manifest.")
    parser.add_argument(
        "--retries", type=int, default=None,
        help="Sets the number of times a failed extension download should be retried before skipping it.")
    parser.add_argument(
        "--skip-failed", type=_parse_bool, default=None,
        help="Sets whether to skip failed downloads or exit on failure.")
    parser.add_argument(
        "--log-level", type=str, default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Sets the level of detail of log messages.")
    parser.add_argument(
        "--log-file", type=str, default=None,
        help=(
            "Sets the file to output log messages to. This flag will override the location set in configuration files "
            "but logs may still be written to syslog and/or stdout."
        ))
    args = parser.parse_args()

    return orchestrator.run(config_path=args.config,
                            include_extensions=args.include_extensions,
                            exclude_extensions=args.exclude_extensions,
                            output_dir=args.output_dir,
                            name_template=args.name_template,
                            retries=args.retries,
                            skip_failed=args.skip_failed,
                            log_level=args.log_level,
                            log_file=args.log_file)

if __name__ == "__main__":
    raise SystemExit(main())
