import os
import json
import argparse
from utils.plex_server_utilities import PlexInfo
from utils.plex_server_utilities import plex_update_libraries
from utils.file_management_helpers import *

def update_episode_data(directory, json_file, do_recursive=False):
    plex_info = PlexInfo()
    
    # Load episode info from JSON file
    with open(json_file, 'r') as f:
        episode_data = json.load(f)

    if do_recursive:
        mkv_files = get_video_files_from_directory_and_subdirectories(directory)
    else:
        mkv_files = get_video_files_from_directory(directory)
    
    for file in mkv_files:
        episode_number = get_episode_number_from_string(os.path.basename(file))
        if episode_number is None:
            continue
        else:
            episode_string = f'{episode_number}'
            
        if episode_string in episode_data:
            print(f"Updating Plex info for {os.path.basename(file)}")
            update_plex_info(file, episode_data[episode_string], plex_info)

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
    do_recursive = args.recursive

    print("Updating episode information in Plex. . .")
    update_episode_data(directory, json_file, do_recursive=do_recursive)

    # Update the Plex libraries
    plex_update_libraries()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='updateepisodedata', description="Update episode data in Plex from JSON file.")
    parser.add_argument('directory', help='Directory containing the episodes')
    parser.add_argument('json_file', help='JSON file with episode data')
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively search the directory for episodes.')

    args = parser.parse_args()

    main(args)
