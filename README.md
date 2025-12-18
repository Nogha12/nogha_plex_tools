# nogha_plex_tools
Several Python scripts used to manage files for a Plex server. Requires MKVToolNix.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Plex credentials:
   - Copy `.env.example` to and rename to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Plex server URL and access token
      - **IMPORTANT**: Ensure that `.env` is never comitted to version control (it should already be in `.gitingore`)

3. To find your Plex access token:
   - Read Plex's official documentation: https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/