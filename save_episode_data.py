import os
import json
import argparse
from utils.plex_server_utilities import PlexInfo
from utils.file_management_helpers import *

def save_episode_data(directory):
    plex_info = PlexInfo()
    data = {}

    mkv_files = get_video_files_from_directory(directory)

    for file in mkv_files:
        print(f'Getting info from Plex for {os.path.basename(file)}')
        episode_info = plex_info.get_plex_info(file)
        if episode_info and 'episode' in episode_info:
            episode_number = episode_info['episode']
            data[episode_number] = episode_info

    output_file = os.path.join(directory, "episode_info.json")

    print("Saving data to JSON. . .")
    with open(output_file, 'x') as f:
        json.dump(data, f, indent=4)

def main(args):
    directory = args.directory

    print("Getting episode information from Plex and saving. . .")
    save_episode_data(directory)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='saveepisodedata', description="Extract episode data from Plex and save to a file.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    
    args = parser.parse_args()

    main(args)