import argparse
from . import orchestrator

def main() -> int:
    parser = argparse.ArgumentParser(prog="everfox-downloader")
    parser.add_argument("--config", type=str, default=None)
    parser.add_argument("--extensions", type=str, nargs="+", default=None)
    parser.add_argument("--output-dir", type=str, default=None)
    parser.add_argument("--name-template", type=str, default=None)
    parser.add_argument("--retries", type=int, default=None)
    parser.add_argument("--skip-failed", type=bool, default=None)
    parser.add_argument("--log-level", type=str, default=None)
    parser.add_argument("--log-file", type=str, default=None)
    args = parser.parse_args()

    return orchestrator.run(config_path=args.config,
                            extensions=args.extensions,
                            output_dir=args.output_dir,
                            name_template=args.name_template,
                            retries=args.retries,
                            skip_failed=args.skip_failed,
                            log_level=args.log_level,
                            log_file=args.log_file)

if __name__ == "__main__":
    raise SystemExit(main())
