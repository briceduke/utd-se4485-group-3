import argparse
from . import orchestrator

def main() -> int:
    parser = argparse.ArgumentParser(
        prog="everfox-deployer",
        description=(
            "This is the deployer half (step 2) of a two-part application for collecting and distributing VSCode "
            "extensions across an airgapped environment. This will retrieve the extension archive and manifest "
            "produced by the downloader-packager half from a locally accessible web server, set up the environment, "
            "and install extensions contained in the package."
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
        "--archive-url", type=str, default=None,
        help="Sets the URL to download the extension archive from.")
    parser.add_argument(
        "--manifest-url", type=str, default=None,
        help="Sets the URL to download the extension manifest from.")
    parser.add_argument(
        "--retries", type=int, default=None,
        help="Sets the number of times a failed archive or manifest download should be retried before failing.")
    parser.add_argument(
        "--target-dir", type=str, default=None,
        help="Sets the VSCode extensions-directory to install extensions to.")
    parser.add_argument(
        "--verify-integrity", type=str, default=None,
        choices=["NONE", "WARN", "ERROR"],
        help=(
            "Sets whether extensions contained in the archive should be verified against signatures provided by the "
            "manifest.\n"
            "    NONE  - Do not verify\n"
            "    WARN  - Warn if files do not match\n"
            "    ERROR - Fail if files do not match"
        ))
    parser.add_argument(
        "--dry-run", type=bool, default=None,
        help=(
            "Downloads the archive and manifest, validates system setup, and verifies archived extensions (if "
            "enabled), but does not set up or modify the filesystem nor install extensions."
        ))
    parser.add_argument(
        "--log-level", type=str, default=None, choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Sets the level of detail of log messages.")
    parser.add_argument(
        "--log-file", type=str, default=None,
        help=(
            "Sets the file to output log messages to. This flag will override the location set in configuration files "
            "but logs may still be written to syslog and/or stdout."
        ))
    parser.add_argument(
        "--include-extensions", type=str, nargs="+", default=None, metavar="EXTENSION",
        help=(
            "Includes extensions to be extracted from the archive (if present).\n"
            "Extra extensions are only extracted as long as this flag is supplied; this is not written to a "
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
            "Excludes configured extensions from being extracted from the archive.\n"
            "Extensions are only excluded as long as this flag is supplied; this is not written to a "
            "configuration file.\n"
            "Format matches that of --include-extensions."
        ))
    parser.add_argument(
        "--backup-dir", type=str, default=None,
        help="Sets the location to back up old extensions to.")
    parser.add_argument(
        "--temp-dir", type=str, default=None,
        help=(
            "Sets the temporary working directory for downloading the archive and manifest and extracting and "
            "verifying new extensions before installation."
        ))
    parser.add_argument(
        "--replace-mode", type=str, default=None,
        choices=["NONE", "REPLACE", "CLEAN"],
        help=(
            "Sets how existing extensions in the target installation directory are treated.\n"
            "    NONE    - Do not replace existing extensions.\n"
            "    REPLACE - Replace existing extensions that are not the same version.\n"
            "    CLEAN   - Replace all existing extensions; extensions not extracted from the archive will be removed."
        ))
    #
    parser.add_argument(
        "--preseed-server",
        action="store_true",
        help="Pre-seed the VS Code server on the target (~/.vscode-server/bin/<commit>) from the bundle."
    )
    parser.add_argument(
        "--vscode-commit",
        type=str,
        metavar="HASH",
        help="VS Code client commit hash (from 'code --version'). Required with --preseed-server"
    )
    args = parser.parse_args()

    return orchestrator.run(config_path=args.config,
                            archive_url=args.archive_url,
                            manifest_url=args.manifest_url,
                            target_dir=args.target_dir,
                            verify_integrity=args.verify_integrity,
                            dry_run=args.dry_run,
                            log_level=args.log_level,
                            log_file=args.log_file,
                            include_extensions=args.include_extensions,
                            exclude_extensions=args.exclude_extensions,
                            retries=args.retries,
                            backup_dir=args.backup_dir,
                            temp_dir=args.temp_dir,
                            replace_mode=args.replace_mode,
                            preseed_server=args.preseed_server,
                            vscode_commit=args.vscode_commit,
                            )

if __name__ == "__main__":
    raise SystemExit(main())
