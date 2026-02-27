"""CLI command routing."""

import argparse
import sys

from .commands import greet, rename


def main():
    parser = argparse.ArgumentParser(prog="plex-tools", description="Plex media tools")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Greet command
    greet_parser = subparsers.add_parser("greet", help="Greet someone")
    greet_parser.add_argument("name", nargs="?", default="friend", help="Name to greet")
    greet_parser.add_argument("--count", type=int, default=1, help="Number of times to greet")

    # Rename command
    rename_parser = subparsers.add_parser("rename", help="Rename files using metadata from the file and Plex")
    rename_parser.add_argument("directory", nargs="?", default=".", help="Directory to process")
    rename_parser.add_argument("--recursive", action="store_true", help="Recursively process subdirectories")
    
    args = parser.parse_args()
    
    if args.command == "greet":
        greet.greet(name=args.name, count=args.count)
    elif args.command == "rename":
        rename.rename(directory=args.directory, recursive=args.recursive)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
