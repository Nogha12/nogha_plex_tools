import os
import json
import argparse
import re
from utils.plex_server_utilities import PlexInfo
from utils.file_management_helpers import *

def update_episode_data(directory, json_file):
    plex_info = PlexInfo()
    
    # Load episode info from JSON file
    with open(json_file, 'r') as f:
        episode_data = json.load(f)

    mkv_files = get_video_files_from_directory(directory)
    
    for file in mkv_files:
        episode_number = f'{get_episode_number_from_string(os.path.basename(file))}'
        if episode_number in episode_data:
            print(f"Updating Plex info for {os.path.basename(file)}")
            update_plex_info(file, episode_data[episode_number], plex_info)

def update_plex_info(file_path, episode_info, plex_info):
    # Retrieve the Plex library and find the episode by file path
    for section in plex_info.plex.library.sections():
        for media in section.all():
            if media.type == 'show':
                for episode in media.episodes():
                    for part in episode.iterParts():
                        if os.path.basename(part.file) == os.path.basename(file_path):
                            episode.edit(**{
                                'title.value': episode_info['title'],
                                'title.locked': 1,
                                'originallyAvailableAt.value': episode_info['originally_available_at'],
                                'originallyAvailableAt.locked': 1,
                                'summary.value': episode_info['summary'],
                                'summary.locked': 1
                            })
                            episode.reload()
                            print(f"Updated info for: {file_path}")

def main(args):
    directory = args.directory
    json_file = args.json_file

    print("Updating episode information in Plex. . .")
    update_episode_data(directory, json_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='updateepisodedata', description="Update episode data in Plex from JSON file.")
    parser.add_argument('directory', help='Directory containing the episodes')
    parser.add_argument('json_file', help='JSON file with episode data')

    args = parser.parse_args()

    main(args)
