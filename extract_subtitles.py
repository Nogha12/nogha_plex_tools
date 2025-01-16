import os
import argparse
import subprocess
from utils.file_management_helpers import *

def extract_subtitles_from_files(mkv_files, language=None):
    # Process each file
    for file_path in mkv_files:
        tracks_info = get_tracks_info(file_path)

        subtitles_tracks_info = [track for track in tracks_info if track['type'] == 'subtitles']
        if language:
            subtitles_tracks_info = [track for track in subtitles_tracks_info if track['language'] == language]

        print("Extracting the following subtitles tracks:")
        list_tracks(subtitles_tracks_info)

        output_paths = [] # Keep track of output paths to avoid overwriting files
        for track in subtitles_tracks_info:
            file_extension = get_file_extension(track['codec'])
            if not file_extension:
                print(f"Could not find file extension for {track['codec']}, skipping. . .")
                continue

            track_language = track['language'] if track['language'] != 'und' else None
            is_forced = track['forced_track']
            track_id = track['id']

            output_path = os.path.splitext(file_path)[0] + (f'.{track_language}' if track_language else '') + ('.forced' if is_forced else '')
            if (output_path + f'.{file_extension}') in output_paths:
                output_path += f'.{track_id}'
            output_path += f'.{file_extension}'
            
            output_paths.append(output_path)

            command = f'mkvextract tracks "{file_path}" {track_id}:"{output_path}"'
            subprocess.run(command, shell=True)

    print("Finished extracting subtitles from files.")

def extract_audio_from_files(mkv_files, language=None):
    # Process each file
    for file_path in mkv_files:
        tracks_info = get_tracks_info(file_path)

        subtitles_tracks_info = [track for track in tracks_info if track['type'] == 'audio']
        if language:
            subtitles_tracks_info = [track for track in subtitles_tracks_info if track['language'] == language]

        print("Extracting the following audio tracks:")
        list_tracks(subtitles_tracks_info)

        for track in subtitles_tracks_info:
            file_extension = get_file_extension(track['codec'])
            if not file_extension:
                print(f"Could not find file extension for {track['codec']}, skipping. . .")
                continue

            track_language = track['language'] if track['language'] != 'und' else None
            output_path = os.path.splitext(file_path)[0] + (('.' + track_language) if track_language else '') + ('.' + file_extension)
            track_id = track['id']

            command = f'mkvextract tracks "{file_path}" {track_id}:"{output_path}"'
            subprocess.run(command, shell=True)

    print("Finished extracting subtitles from files.")

def main(args):
    directory = args.directory
    track_type = args.track_type
    language = args.language
    
    if language == 'und':
        language = None

    mkv_files_from_which_to_extract = get_video_files_from_directory(directory)
    if track_type == 'subtitles':
        extract_subtitles_from_files(mkv_files_from_which_to_extract, language=language)
    elif track_type == 'audio':
        extract_audio_from_files(mkv_files_from_which_to_extract, language=language)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvextractsubs', description="Extract all subtitle tracks from the MKV files in a directory.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    parser.add_argument('--track-type', choices=['subtitles', 'audio'], default='subtitles', help='Type of tracks to extract (subtitles or audio)')
    parser.add_argument('--language', default='und', help='Language of tracks to extract (3-letter ISO 639-2 code)', type=str)
    
    args = parser.parse_args()

    # Validate language code
    if not is_valid_language_code(args.language):
        raise ValueError(f"Invalid language code: {args.language}")

    main(args)
