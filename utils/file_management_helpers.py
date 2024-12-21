import os
import re
import subprocess
import json
import pycountry
from plex_server_utilities import PlexInfo

# The pattern for global IDs that input must match
global_id_pattern = re.compile(r'^\d+:\d+$')

def is_valid_language_code(lang_code):
    try:
        # Attempt to get the language by the 3-letter code
        language = pycountry.languages.get(alpha_3=lang_code)
        return language is not None
    except KeyError:
        return False
    
def list_tracks(tracks_info):
    """Display the given tracks info in a readable format."""
    if isinstance(tracks_info, dict):
        tracks_info = [tracks_info]

    for track in tracks_info:
        print(f"  ID: {track['file_id']}:{track['id']}, Type: {track['type']}, Language: {track['language']}, Codec: {track['codec']}, Name: {track['track_name']}")

def get_file_extension(codec):
    # Dictionary mapping codecs to their corresponding file extensions
    codec_to_extension = {
        "SubStationAlpha": "ass",
        "SSA": "ssa",
        "SRT": "srt",
        "VobSub": "sub",
        "HDMV PGS": "sup",
        "PGS": "sup",
        "AC-3": "ac3",
        "E-AC-3": "eac3",
        "AAC": "aac",
        "DTS": "dts",
        "FLAC": "flac",
        "MP3": "mp3",
        "Opus": "opus",
        "Vorbis": "ogg",
        "H.264": "h264",
        "H.265": "hevc",
        "HEVC": "hevc",
        "AV1": "av1",
        # Add more mappings as needed
    }

    # Split the codec string by slashes and check each part
    for part in codec.split('/'):
        if part in codec_to_extension:
            return codec_to_extension[part]
    
    # Return None if no match is found
    return None

def get_tracks_info(file_path, file_id=0):
    """Get track information of a .mkv file using mkvmerge."""
    try:
        command = f'mkvmerge -J "{file_path}"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True, encoding='utf-8')
        output = result.stdout
        data = json.loads(output)

        # Check the file name for language or forced tags
        file_tags = os.path.basename(file_path).lower().split('.')[1:-1]
        forced = 'forced' in file_tags
        language = 'und' # 'und' for undefined
        for tag in file_tags:
            if is_valid_language_code(tag):
                language = tag
                break
        
        # Extract relevant track information
        tracks_info = []
        for number, track in enumerate(data['tracks'], start=1):
            track_info = {
                'file_id': file_id,
                'number': number,
                'id': track['id'],
                'type': track['type'],
                'codec': track['codec'],
                'pixel_dimensions': track['properties'].get('pixel_dimensions', 'N/A'),
                'language': track['properties'].get('language', language),  
                'default_track': track['properties'].get('default_track', False),
                'forced_track': track['properties'].get('forced_track', forced),
                'flag_original': track['properties'].get('flag_original', False),
                'flag_hearing_impaired': track['properties'].get('flag_hearing_impaired', False),
                'flag_visual_impaired': track['properties'].get('flag_visual_impaired', False),
                'flag_text_descriptions': track['properties'].get('flag_text_descriptions', False),
                'flag_commentary': track['properties'].get('flag_commentary', False),
                'track_name': track['properties'].get('track_name', 'N/A')
            }
            tracks_info.append(track_info)
        
        return tracks_info
    except Exception as e:
        print(f"Error extracting info from {file_path}: {e}")
        return None


def get_identifying_info_from_tracks_info(tracks_info):
    identifying_tracks_info = [
        {key: track[key] for key in ('file_id', 'id', 'type', 'language')}
        for track in tracks_info
    ]
    return identifying_tracks_info
    
def get_matching_files_from_directory(directory):
    """Analyze .mkv files in the directory and its subdirectories and return a list of files with matching track structures."""
    mkv_files = get_mkv_files_from_directory(directory)

    if not mkv_files:
        print("No .mkv files were found in the directory.")
        return

    first_file_info = get_tracks_info(mkv_files[0])
    if first_file_info is None:
        print(f"Error reading tracks info from {mkv_files[0]}. Aborting.")
        return
    
    print(f"Checking that all files have the same track structure as the following: {os.path.basename(mkv_files[0])}")
    expected_file_info = get_identifying_info_from_tracks_info(first_file_info)

    matching_mkv_files = [mkv_files[0]]
    for file_path in mkv_files[1:]:
        file_info = get_tracks_info(file_path)
        if file_info is None:
            continue
        
        if get_identifying_info_from_tracks_info(file_info) == expected_file_info:
            matching_mkv_files.append(file_path)
        else:
            print(f"File {os.path.basename(file_path)} has a different track structure or order of language tags.")

    print(f"{len(matching_mkv_files)} matching .mkv files have been found.")

    return matching_mkv_files

def get_mkv_files_from_directory(directory):
    mkv_files = []
    for file in os.listdir(directory):
        if file.endswith('.mkv'):
            mkv_files.append(os.path.join(directory, file))
    return mkv_files