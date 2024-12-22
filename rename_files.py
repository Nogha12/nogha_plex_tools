import os
import re
import argparse
from utils.plex_server_utilities import PlexInfo
from utils.file_management_helpers import *

# Invalid characters for Windows filenames
invalid_chars = '<>:"/\\|?*'

# Function to check if text contains characters that cannot be in a filename
def is_valid_filename_text(text):
    return not any(char in invalid_chars for char in text)

def is_valid_title(text):
    if not is_valid_filename_text(text): return False

    # Titles shouldn't contian square brackets or space-dash-space
    pattern = re.compile(r'[\[\]]| - ')
    return not bool(pattern.search(text))

def is_valid_resolution(text):
    if not is_valid_filename_text(text): return False

    pattern = re.compile(r'^\d+[ip]$')
    return bool(pattern.match(text))

def is_valid_codec(text):
    known_codecs = ["HEVC", "AV1", "H.264", "MPEG-4p2"] # add more as needed
    return text in known_codecs

def rename_files(episode_files_data, series_name, encoder_name):
    renaming_is_approved = False

    # Loop through the files in the directory
    for file_info in episode_files_data:
        file_path = file_info['file_path']
        # Construct the SXXEXX identifier with the season and episode information
        se_identifier = f"S{file_info['season']:02}E{file_info['episode']:02}"

        # Check that the title is valid for a file name and prompt the user if not
        plex_title = file_info['title']

        # Remove trailing question mark if present
        if plex_title.endswith('?') and not plex_title.endswith(' ?'):
            title = plex_title[:-1]
        else:
            title = plex_title

        if not is_valid_title(title):
            print(f"Title \"{title}\" contains characters not valid for a file name or contains a space-dash-space. Manual entry required.")
            while True:
                # Prompt the user for the episode title
                title_input = input(f'Please enter the corrected title for {se_identifier}: ').strip()
                if is_valid_title(title_input):
                    title = title_input
                    break
                else:
                    print(f'Title contains invalid characters. Please avoid using {invalid_chars} or invalid sequences.')

        # Convert the pixel dimensions to a vertical resolution (e.g. 1080p)
        horizontal_resolution, vertical_resolution = file_info['pixel_dimensions'].split('x')
        horizontal_resolution = int(horizontal_resolution)
        vertical_resolution = int(vertical_resolution)
        # Ultra-wide resolutions (wider than 16:9) get normalized
        if (horizontal_resolution/vertical_resolution) > (16/9):
            normalized_vertical_resolution = round(horizontal_resolution*(9/16))
            resolution = f"{normalized_vertical_resolution}p"
        else:
            resolution = f"{vertical_resolution}p"
        assert is_valid_resolution(resolution)

        # Ensure that the codec is in the proper form (should be HEVC, H.264, or AV1)
        codec_full = file_info['codec']
        codec_list = codec_full.split('/')
        for codec_name in codec_list:
            if is_valid_codec(codec_name):
                codec = codec_name
                break
        if not codec:
            raise RuntimeError

        # Construct the new filename
        output_file_name = f"{series_name} - {se_identifier} - {title} [{resolution}][{codec}][{encoder_name}].mkv"

        # Get full path
        dir_path = os.path.dirname(file_path)
        output_path = os.path.join(dir_path, output_file_name)
        
        # if not (SERIES and season and episode and title and resolution and codec and encoder):
        #     raise ValueError("One of the file name parts failed to load.")
        
        # Rename the file
        print(f'Renaming "{os.path.basename(file_path)}" to "{output_file_name}"')
        if not renaming_is_approved:
            user_input = input("Go ahead with renaming all files in this manner? (type 'y' or 'yes'): ").strip().lower()
            if user_input in ['y', 'yes']:
                renaming_is_approved = True
            else: return
        os.rename(file_path, output_path)

def get_files_information(directory, do_recursive=False):
    """Create a list of .mkv file path names along with episode number, season number, title, resolution, and codec"""
    # Create a PlexInfo object from which to extract information about each file from Plex
    plex_agent = PlexInfo()
    # Get the paths of all the mkv files to rename
    if do_recursive:
        video_files_to_rename = get_video_files_from_directory_and_subdirectories(directory)
    else:
        video_files_to_rename = get_video_files_from_directory(directory)

    if not video_files_to_rename:
        return None

    video_files_info = []
    for filepath in video_files_to_rename:
        # From Plex, grab the episode number, season number, and title
        plex_info = plex_agent.get_plex_info(filepath)
        # Using mkvmerge, grab the video codec and resolution
        tracks_info = get_tracks_info(filepath)
        video_track_info = [track for track in tracks_info if track['type'] == 'video'][0]

        try:
            file_info = {
                'file_path': filepath,
                'season': plex_info['season'],
                'episode': plex_info['episode'],
                'title': plex_info['title'],
                'pixel_dimensions': video_track_info['pixel_dimensions'],
                'codec': video_track_info['codec'],
            }
        except TypeError as e:
            print(f'Error found when parsing file info: {e}')
            print("Error most likely caused by Plex info not being updated. Make sure the files are known to Plex and parsed by the correct agent.")
            return

        video_files_info.append(file_info)
        print(f"Successfully retreived information for {os.path.basename(filepath)}.")
    
    return video_files_info


def main(args):
    directory = args.directory
    do_recursive = args.recursive

    # Get the paths of all MKV files in the directory along with relevant information
    print(f"Scanning .mkv files in {directory}. . .")
    files_info = get_files_information(directory, do_recursive=do_recursive)

    if not files_info:
        print("No MKV files found in the directory.")
        return

    # Prompt the user for the series name
    while True:
        series = input(f'Please enter the name of the SERIES for all files in {directory}: ').strip()
        if is_valid_title(series):
            break
        else:
            print(f'Name contains invalid characters. Please avoid using {invalid_chars} or invalid sequences.')
    
    # Prompt the user for the encoder's name
    while True:
        encoder = input(f'Please enter the name of the ENCODER for all files in {directory}: ').strip()
        if is_valid_filename_text(encoder):
            break
        else:
            print(f'Name contains invalid characters. Please avoid using {invalid_chars}.')
    
    rename_files(files_info, series, encoder)

    print("Done!")
    return

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvrenamer', description="Rename the MKV files in the directory according to the Plex standard.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    parser.add_argument('-r', '--recursive', action='store_true', help='Recursively search the directory for video files.')
    
    args = parser.parse_args()
    main(args)
