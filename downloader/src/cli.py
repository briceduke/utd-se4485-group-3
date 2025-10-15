import argparse
from . import orchestrator

def main() -> int:
    parser = argparse.ArgumentParser(prog="everfox-downloader")
    parser.add_argument("--config", type=str, default=None)
    # TODO: add all arguments
    args = parser.parse_args()
    return orchestrator.run(args.config)

if __name__ == "__main__":
    raise SystemExit(main())
