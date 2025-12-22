"""CLI command routing."""

import argparse
import sys

from .commands import greet


def main():
    parser = argparse.ArgumentParser(prog="plex-tools", description="Plex media tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Greet command
    greet_parser = subparsers.add_parser("greet", help="Greet someone")
    greet_parser.add_argument("name", nargs="?", default="friend", help="Name to greet")
    greet_parser.add_argument("--count", type=int, default=1, help="Number of times to greet")
    
    args = parser.parse_args()
    
    if args.command == "greet":
        greet.greet(name=args.name, count=args.count)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
