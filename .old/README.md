# Legacy Code Archive

This directory contains the original standalone Python scripts from before the CLI refactoring.

These are kept for reference and historical purposes, but should NOT be used. The new CLI-based tools provide the same functionality with better organization and error handling.

## Migration Guide

The following legacy scripts have been migrated to CLI commands:

| Legacy Script | New CLI Command |
|---|---|
| `remux_files.py` + `edit_tracks_properties.py` | `plex-tools process` |
| `rename_files.py` | `plex-tools rename` |
| `extract_subtitles.py` | `plex-tools extract` |
| `verify_files.py` | `plex-tools verify` |
| `save_episode_data.py` | `plex-tools data save` |
| `load_episode_data.py` | `plex-tools data load` |
| `extract_episode_artwork.py` | `plex-tools extract-artwork` |

All git history is preserved, so you can still `git log` to see changes to these files.

# nogha_plex_tools
Several Python scripts used to manage files for a Plex server. Requires MKVToolNix.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Plex credentials:
   - Copy `.env.example` and rename it to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Plex server URL and access token
      - **IMPORTANT**: Ensure that `.env` is never comitted to version control (it should already be in `.gitingore`)

3. To find your Plex access token:
   - Read Plex's official documentation: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/
