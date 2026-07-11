import argparse
import logging
import sys
from pathlib import Path

VERSION = "1.0.0"


def _setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "secpass.log"),
            logging.StreamHandler(sys.stdout),
        ],
        force=True,
    )


def main():
    parser = argparse.ArgumentParser(description="SecPass - Password Manager")
    parser.add_argument("--version", action="store_true", help="Show version and exit")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    args, _ = parser.parse_known_args()

    if args.version:
        print(f"SecPass Free {VERSION}")
        sys.exit(0)

    if args.debug:
        _setup_logging()

    from gui.main_window import main as gui_main

    gui_main()


if __name__ == "__main__":
    main()
