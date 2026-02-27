"""Rename files using metadata from the file and Plex."""

from plex_tools.operations.plex_server_utilities import plex_update_libraries


def rename(directory: str, recursive: bool = False):
    plex_update_libraries()

    return
