# nogha_plex_tools
Several Python scripts used to manage files for a Plex server. Requires MKVToolNix.

## Setup

1. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure Plex credentials:
   - Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   - Edit `.env` and add your Plex server URL and access token
   - **IMPORTANT**: Never commit `.env` to version control (it's in `.gitignore`)

3. To find your Plex access token:
   - Go to https://app.plex.tv/
   - Open Developer Tools (F12)
   - Check Network tab and refresh the page
   - Look for requests to plex.tv and check the `X-Plex-Token` header
   - Or visit: https://support.plex.tv/articles/204059436-finding-an-auth-token-and-local-ip/