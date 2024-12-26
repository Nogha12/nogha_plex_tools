import os
import re
import subprocess
import json
import pycountry

# The pattern for global IDs that input must match
global_id_pattern = re.compile(r'^\d+:\d+$')

def is_valid_language_code(lang_code):
    try:
        # Attempt to get the language by the 3-letter code
        language = pycountry.languages.get(alpha_3=lang_code)
        if not language:
            # If not found, try to get the language by the 2-letter code
            language = pycountry.languages.get(alpha_2=lang_code)
        elif not language:
            # If not found, try to get the language by the name
            language = pycountry.languages.get(name=lang_code)
        return language is not None
    except KeyError:
        return False
    
def list_tracks(tracks_info):
    """Display the given tracks info in a readable format."""
    if isinstance(tracks_info, dict):
        tracks_info = [tracks_info]

    for track in tracks_info:
        track_info_sring = f"  ID: {track['file_id']}:{track['id']}, Type: {track['type']}, Language: {track['language']}, Codec: {track['codec']}"
        if track['track_name'] != 'N/A':
            track_info_sring += f", Name: {track['track_name']}"
        else:
            # If another track file name has the same base name, include parent directory in the file name
            file_name = os.path.basename(track['file_name'])
            if any(file_name in os.path.basename(other_track['file_name']) for other_track in tracks_info if other_track['file_id'] != track['file_id']):
                file_name = os.path.join(os.path.basename(os.path.dirname(track['file_name'])), file_name)

            track_info_sring += f", Source filename: {file_name}"
        print(track_info_sring)

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
        "MPEG-4p2": "mp4"
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
                'file_name': file_path,
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
    
def get_episode_number_from_string(search_string):
    """Search the given string to see if it contains an episode number and return it if so."""
    # Check the basic case where there is a string of the form sXXeYY
    match = re.search(r'\bs\d{1,2}e(\d{1,3})', search_string, re.IGNORECASE)
    if match:
        return int(match.group(1))
    
    # Check for cases where the episode number follows "episode", "ep", or 'e' separated by a space, dot, dash, underscore, or nothing
    match = re.search(r'(episode|ep|\be)[ _.-]?(\d{1,3})', search_string, re.IGNORECASE)
    if match:
        return int(match.group(2))
    
    # Check for the case where there is only a single number in the string
    matches = re.findall(r'\b(\d{1,3})\b', search_string)
    if len(matches) == 1:
        return int(match.group(1))
    
    ## Consider adding more checks here

    return None


def get_identifying_info_from_tracks_info(tracks_info):
    identifying_tracks_info = [
        {key: track[key] for key in ('file_id', 'id', 'type', 'language')}
        for track in tracks_info
    ]
    return identifying_tracks_info
    
def get_matching_files_from_directory(directory, recursive=False):
    """Analyze video files in the directory and its subdirectories and return a list of video files with matching track structures."""
    if recursive:
        video_files = get_video_files_from_directory_and_subdirectories(directory)
    else:
        video_files = get_video_files_from_directory(directory)

    if not video_files:
        print("No .mkv, .mp4, or .avi files were found in the directory.")
        return

    first_file_info = get_tracks_info(video_files[0])
    if first_file_info is None:
        print(f"Error reading tracks info from {video_files[0]}. Aborting.")
        return
    
    print(f"Checking that all files have the same track structure as the following: {os.path.basename(video_files[0])}")
    expected_file_info = get_identifying_info_from_tracks_info(first_file_info)

    matching_video_files = [video_files[0]] # intialize with the first file
    for file_path in video_files[1:]:
        file_info = get_tracks_info(file_path)
        if file_info is None:
            continue
        
        if get_identifying_info_from_tracks_info(file_info) == expected_file_info:
            matching_video_files.append(file_path)
        else:
            print(f"File {os.path.basename(file_path)} has a different track structure or order of language tags.")

    print(f"{len(matching_video_files)} matching video files have been found.")

    return matching_video_files

def get_video_files_from_directory(directory):
    """Return a list of all .mkv, .mp4, or .avi files in the given directory."""
    video_files = []
    for file in os.listdir(directory):
        if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
            video_files.append(os.path.join(directory, file))
    return video_files

def get_video_files_from_directory_and_subdirectories(directory):
    """Return a list of all .mkv, .mp4, or .avi files in the given directory and its subdirectories."""
    video_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.mkv') or file.endswith('.mp4') or file.endswith('.avi'):
                video_files.append(os.path.join(root, file))
    return video_files