import os
import argparse
import urllib.request
from utils.file_management_helpers import *
from utils.plex_server_utilities import *

# Iterate through files in the directory
def extract_episode_artworks(directory):
    # Create a PlexInfo object from which to extract information about each file from Plex
    plex_agent = PlexInfo()

    mkv_files = get_video_files_from_directory(directory)

    for file in mkv_files:
        # Create path for the artwork
        output_path = os.path.splitext(file)[0] + '.jpg'

        plex_info = plex_agent.get_plex_info(file)

        show_search = plex_agent.plex.library.search(plex_info['series'])
        for result in show_search:
            if result.title == plex_info['series']:
                show_item = result
                break

        episode_item = show_item.season(plex_info['season']).episode(plex_info['episode'])
        artwork_path = episode_item.thumb
        artwork_url = f'{PLEX_SERVER_BASE_URL}{artwork_path}?X-Plex-Token={PLEX_ACESS_TOKEN}'
        urllib.request.urlretrieve(artwork_url, output_path)

        print(f'Artwork saved as: {os.path.basename(output_path)}')

def extract_season_artwork(directory):
    # Create a PlexInfo object from which to extract information from Plex
    plex_agent = PlexInfo()

    mkv_files = get_video_files_from_directory(directory)

    first_file = mkv_files[0]

    plex_info = plex_agent.get_plex_info(first_file)

    show_item = None
    show_search = plex_agent.plex.library.search(plex_info['series'])
    for result in show_search:
        if result.title == plex_info['series']:
            show_item = result
            break

    assert show_item, f"Could not find show {plex_info['series']} in Plex."

    season_item = show_item.season(plex_info['season'])
    
    # Create path for the artwork
    output_path = os.path.join(directory, f'Season{plex_info["season"]:02}.jpg')
    artwork_path = season_item.thumb
    artwork_url = f'{PLEX_SERVER_BASE_URL}{artwork_path}?X-Plex-Token={PLEX_ACESS_TOKEN}'
    urllib.request.urlretrieve(artwork_url, output_path)

    print(f'Artwork saved as: {os.path.basename(output_path)}')

def main(args):
    directory = args.directory
    get_season_artwork = args.season

    if get_season_artwork:
        print("Extracting season artwork. . .")
        extract_season_artwork(directory)
    else:
        print("Extracting episode artwork. . .")
        extract_episode_artworks(directory)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvextractsubs', description="Extract all subtitle tracks from the MKV files in a directory.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    parser.add_argument('--season', action='store_true', help='Extract season artwork instead of episode artwork')
    
    args = parser.parse_args()

    main(args)
