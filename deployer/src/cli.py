import argparse
from . import orchestrator

def main() -> int:
    parser = argparse.ArgumentParser(prog="everfox-deployer")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--archive-url", type=str, default=None)
    parser.add_argument("--target-dir", type=str, default=None)
    parser.add_argument("--verify-integrity", type=str, default=None)
    parser.add_argument("--dry-run", type=bool, default=None)
    parser.add_argument("--log-level", type=str, default=None)
    parser.add_argument("--log-file", type=str, default=None)
    parser.add_argument("--include-extensions", type=str, nargs="+", default=None)
    parser.add_argument("--exclude-extensions", type=str, nargs="+", default=None)
    parser.add_argument("--retries", type=int, default=None)
    parser.add_argument("--backup-dir", type=str, default=None)
    parser.add_argument("--temp-dir", type=str, default=None)
    parser.add_argument("--replace-mode", type=str, default=None)
    args = parser.parse_args()

    return orchestrator.run(config_path=args.config,
                            archive_url=args.archive_url,
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
                            replace_mode=args.replace_mode)

if __name__ == "__main__":
    raise SystemExit(main())
