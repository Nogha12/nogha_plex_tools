import os
import re
import argparse
import subprocess
from shutil import copyfile
from utils.file_management_helpers import *
from utils.plex_server_utilities import PlexInfo
from utils.prompt_helpers import *
from edit_tracks_properties import update_track_properties

def is_muxable_extension(file_extension):
    file_extension = re.sub(r'\.', '', file_extension).strip()
    # Dictionary mapping codecs to their corresponding file extensions
    muxable_extensions = [
        "ass",
        "ssa",
        "srt",
        "sub",
        "sup",
        "ac3",
        "eac3",
        "aac",
        "dts",
        "flac",
        "mp3",
        "opus",
        "ogg",
        "h264",
        "hevc",
        "hevc",
        "av1",
        "mp4",
        "mkv",
        # Add more mappings as needed
    ]

    return file_extension in muxable_extensions

def prompt_for_tracks_order(tracks_info, enforce_track=True):
    """Ask the user for the order of the given tracks."""
    present_global_ids = [f'{track["file_id"]}:{track["id"]}' for track in tracks_info]

    # If there is only 1 track and there must be a track of this type, automatically select it.
    if enforce_track and len(present_global_ids) == 1:
        new_order = present_global_ids
    else:
        # Prompt the user to provide the order of the tracks
        print("Enter the new ORDER of track IDs (int:int), separated by commas:")
        while True:
            try:
                new_order = input().strip().split(',')
                new_order = [id.strip() for id in new_order if id]
                if len(new_order) >= 1:
                    for id in new_order:
                        if not bool(global_id_pattern.match(id)):
                            print(f"The ID provided, {id}, is not of the form int:int. Try again:")
                            raise ValueError
                        if id not in present_global_ids:
                            print(f"The ID provided, {id}, is not one of the IDs to be sorted. Try again:")
                            raise ValueError
                elif enforce_track:
                    print(f'You must include at least one track in the new sorting.')
                    raise ValueError
                else:
                    new_order = []
                break
            except ValueError:
                continue

    # Remove the tracks that were not included in the ordering
    reduced_tracks = [track for track in tracks_info if f'{track["file_id"]}:{track["id"]}' in new_order]

    # Reorder tracks
    reordered_tracks = sorted(reduced_tracks, key=lambda t: new_order.index(f'{t["file_id"]}:{t["id"]}'))

    return reordered_tracks

def prompt_for_new_tracks_info(list_of_tracks_info, force_language_prompt=False, ask_for_additional_flags=False):
    """Ask the user for the new order of tracks and which tracks should be default or forced."""
    # Split the tracks_info into video, audio, subtitles, and other
    video_tracks_info = []
    audio_tracks_info = []
    subtitles_tracks_info = []
    other_tracks_info = []

    for tracks_info in list_of_tracks_info:
        video_tracks_info += [track for track in tracks_info if track['type'] == 'video']
        audio_tracks_info += [track for track in tracks_info if track['type'] == 'audio']
        subtitles_tracks_info += [track for track in tracks_info if track['type'] == 'subtitles']
        other_tracks_info += [track for track in tracks_info if track['type'] not in ['video', 'audio', 'subtitles']]

    # Ensure there is only 1 video track
    if len(video_tracks_info) > 1:
        print("There is more than one video track:")
        
        video_global_ids = [f'{track["file_id"]}:{track["id"]}' for track in video_tracks_info]

        list_tracks(video_tracks_info)

        while True:
            video_track_id = input("Enter the ID of the video track that should be kept: ").strip()
            if not bool(global_id_pattern.match(video_track_id)):
                print(f"The ID provided, {video_track_id}, is not of the form int:int. Try again:")
                continue
            if video_track_id not in video_global_ids:
                print(f"The ID provided, {video_track_id}, is not one of the video IDs.")
                continue
            break

        video_tracks_info = [track for track in video_tracks_info if f'{track["file_id"]}:{track["id"]}' == video_track_id]
    
    # VIDEO TRACK
    # Set video track tags to their assumed values
    video_tracks_info[0]['default_track'] = True
    video_tracks_info[0]['forced_track'] = False
    video_tracks_info[0]['language'] = 'und'
    video_tracks_info[0]['flag_original'] = False
    video_tracks_info[0]['flag_visual_impaired'] = False
    video_tracks_info[0]['flag_commentary'] = False
    video_tracks_info[0]['flag_hearing_impaired'] = False
    video_tracks_info[0]['flag_text_descriptions'] = False
    video_tracks_info = prompt_for_tracks_names(video_tracks_info)

    # AUDIO TRACKS
    # Prompt for audio order and default/forced track
    print("\nAudio tracks:")
    list_tracks(audio_tracks_info)
    audio_tracks_info = prompt_for_tracks_order(audio_tracks_info, enforce_track=True)
    list_tracks(audio_tracks_info)
    audio_tracks_info = prompt_for_tracks_flags(audio_tracks_info, enforce_default=True, ask_for_forced=False, ask_for_additional_audio_flags=ask_for_additional_flags)
    audio_tracks_info = prompt_for_tracks_languages(audio_tracks_info, force_language_prompt=force_language_prompt)
    audio_tracks_info = prompt_for_tracks_names(audio_tracks_info)

    # SUBTITLES TRACKS
    # Prompt for subtitles order and default/forced track
    if subtitles_tracks_info:
        print("\nSubtitles tracks:")
        list_tracks(subtitles_tracks_info)
        subtitles_tracks_info = prompt_for_tracks_order(subtitles_tracks_info, enforce_track=False)
        list_tracks(subtitles_tracks_info)
        subtitles_tracks_info = prompt_for_tracks_flags(subtitles_tracks_info, enforce_default=False, ask_for_forced=True, ask_for_additional_subtitles_flags=ask_for_additional_flags)
        subtitles_tracks_info = prompt_for_tracks_languages(subtitles_tracks_info, force_language_prompt=force_language_prompt)
        subtitles_tracks_info = prompt_for_tracks_names(subtitles_tracks_info)

    updated_tracks_info = video_tracks_info + audio_tracks_info + subtitles_tracks_info + other_tracks_info

    # Update the 'number' field to be the new order (1-indexed)
    for number, track in enumerate(updated_tracks_info, start=1):
        track['number'] = number

    return updated_tracks_info

def add_matches_from_second_directory(file_matches, second_directory):
    # Create a PlexInfo object from which to extract information about each file from Plex
    plex_agent = PlexInfo()

    # Put the MKV files from the second directory in a dictionary indexed by their episode number
    print("Matching episodes from the second directory to the primary. . .")
    second_dir_mkv_files = get_matching_files_from_directory(second_directory)
    second_dir_dict = {}
    for file in second_dir_mkv_files:
        plex_info = plex_agent.get_plex_info(file)
        episode_number = plex_info['episode']
        second_dir_dict[episode_number] = file

    # Add matching episodes from the second directory into the corresponding file_matches list
    for matches in file_matches:
        for file in matches:
            if file.endswith('.mkv'):
                plex_info = plex_agent.get_plex_info(file)
                episode_number = plex_info['episode']
                matching_episode = second_dir_dict[episode_number]
                matches.append(matching_episode)
                break

    return file_matches

def mux_files(file_paths, tracks_info, output_path, attachments=[], subtitles_delay=0):
    """Remux the files to reorder tracks using mkvmerge."""
    # Separate the different types of tracks
    video_tracks_info = [track for track in tracks_info if track['type'] == 'video']
    audio_tracks_info = [track for track in tracks_info if track['type'] == 'audio']
    subtitles_tracks_info = [track for track in tracks_info if track['type'] == 'subtitles']
    
    # Comma-separated IDs for the track order argument
    track_order_ids = ','.join(f'{track["file_id"]}:{track["id"]}' for track in tracks_info)
    
    command = f'mkvmerge --track-order {track_order_ids}'

    for attachment in attachments:
        command += f' --attach-file "{attachment}"'

    command += f' -o "{output_path}"'

    for file_id, file_path in enumerate(file_paths):
        # Comma-separated IDs for the tracks command arguments
        video_tracks_ids = ','.join(f'{track["id"]}' for track in video_tracks_info if track["file_id"] == file_id)
        audio_tracks_ids = ','.join(f'{track["id"]}' for track in audio_tracks_info if track["file_id"] == file_id)
        subtitles_tracks_ids = ','.join(f'{track["id"]}' for track in subtitles_tracks_info if track["file_id"] == file_id)

        # Append arguments to the command for each file
        if video_tracks_ids:
            command += f' --video-tracks {video_tracks_ids}'
        else:
            command += f' --no-video'
        if audio_tracks_ids:
            command += f' --audio-tracks {audio_tracks_ids}'
        else:
            command += f' --no-audio'
        if subtitles_tracks_ids:
            command += f' --subtitle-tracks {subtitles_tracks_ids}'
            if subtitles_delay != 0:
                for track in subtitles_tracks_info:
                    if track['file_id'] == file_id:
                        command += f' --sync {track["id"]}:{subtitles_delay}'
        else:
            command += f' --no-subtitles'
        command += f' "{file_path}"'
    
    # Run the command
    subprocess.run(command, shell=True)

def get_font_attachments(directory):
    font_attchments = []
    for file in os.listdir(directory):
        if file.lower().endswith(('.ttf', '.otf')):
            font_attchments.append(os.path.join(directory, file))
    return font_attchments

def mux_files_into_mkv(file_matches, attachments=[], force_language_prompt=False, ask_for_additional_flags=False, subtitles_delay=0):
    first_matching_files = file_matches[0]

    # This is a list of tracks info for all the tracks to merge
    first_matching_files_tracks_infos = []

    for file_id, file in enumerate(first_matching_files):
        tracks_info = get_tracks_info(file, file_id=file_id)
        first_matching_files_tracks_infos.append(tracks_info)
    
    # Prompt the user to give the new order and default/forced status for the tracks
    tracks_template = prompt_for_new_tracks_info(first_matching_files_tracks_infos, force_language_prompt=force_language_prompt, ask_for_additional_flags=ask_for_additional_flags)
    
    print("\nUsing the following template to update tracks info in all .mkv files:")
    for track in tracks_template:
        print(track)

    user_input = input("Go ahead with editing all the tracks to this format? (type 'y' or 'yes'): ").strip().lower()
    if user_input not in ['y', 'yes']:
        print("Aborting. . .")
        return

    # Process each file
    for file_paths in file_matches:
        # Determine the new output path for remuxed files
        for file_path in file_paths:
            if file_path.lower().endswith('.mkv') or file_path.lower().endswith('.mp4') or file_path.lower().endswith('.avi'):
                main_file_path = file_path
                break # break here because the primary video file should be listed before other video files.
        new_dir = os.path.join(os.path.dirname(main_file_path), 'remux')
        os.makedirs(new_dir, exist_ok=True)
        output_path = os.path.join(new_dir, os.path.basename(main_file_path))
        
        # Check if remuxing is needed
        if (
            (get_identifying_info_from_tracks_info(tracks_template) != get_identifying_info_from_tracks_info(get_tracks_info(file_paths[0]))) 
            or (subtitles_delay != 0)
        ):
            mux_files(file_paths, tracks_template, output_path, attachments=attachments, subtitles_delay=subtitles_delay)
        else:
            # If no reordering is needed, just copy the file
            copyfile(file_paths[0], output_path)

        # Update track properties
        update_track_properties(output_path, tracks_template, set_additional_flags=ask_for_additional_flags)

    print("Finished remuxing files.")

def path_to_match_name(file_path):
    """Take a full file path and strip away the directory, extension, and any extra tags to get a match name."""
    # Remove the directory
    base_name = os.path.basename(file_path)
    # Remove the extension
    match_name = os.path.splitext(base_name)[0]

    return string_to_match_name(match_name)

def string_to_match_name(string_to_convert):
    """Take a full file path and strip away the directory, extension, and any extra tags to get a match name."""
    # Remove tags inside of brackets
    match_name = re.sub(r'\[.*?\]', '', string_to_convert).strip()
    # Remove additional tags
    tags = re.findall(r'\.\w{2,}(\.|$)', match_name)
    for tag in tags:
        if is_valid_language_code(tag[1:]) or tag[1:] == 'forced':
            match_name = match_name.replace(tag, '')

    return match_name

def get_tracks_to_mux(main_files):
    """Return a list of lists of files that should be muxed together."""
    plex_agent = PlexInfo()
    file_matches = []
    for file in main_files:
        directory = os.path.dirname(file)

        # Get a "match name" for the file which consists of its base name without the extension and any extra tags
        match_name = path_to_match_name(file)

        # Check if the file exists in Plex and get the episode number
        plex_info = plex_agent.get_plex_info(file)
        if plex_info:
            try:
                episode_number = int(plex_info['episode'])
            except KeyError:
                episode_number = None
        else:
            episode_number = None

        matching_files = []

        # Loop through the files in the directory of the current file to find matches
        for other_file in os.listdir(directory):
            # Check if the file is muxable
            file_extension = os.path.splitext(other_file)[1]
            if is_muxable_extension(file_extension):
                # Check if the match name is the same as the main file
                other_file_match_name = path_to_match_name(other_file)
                if other_file_match_name == match_name:
                    matching_files.append(os.path.join(directory, other_file))
                    continue

                # Check if the episode number is the same as the main file
                if episode_number:
                    other_file_episode_number = get_episode_number_from_string(other_file_match_name)
                    if other_file_episode_number == episode_number:
                        matching_files.append(os.path.join(directory, other_file))
                        continue

        # Check all subdirectories for directories with the same name as the match name
        for root, dirs, files in os.walk(directory):
            for dir in dirs:
                if string_to_match_name(dir) == match_name:
                    # Append all files in the folder to the matching_files list
                    for file in os.listdir(os.path.join(root, dir)):
                        matching_files.append(os.path.join(root, dir, file))

        file_matches.append(matching_files)

    # Verify that the matching_files lists are all the same length
    for matching_files in file_matches:
        if len(matching_files) != len(file_matches[0]):
            print("Error: The file matches lists are not all the same length.")
            return
    print(f'Found {len(file_matches[0])} matching files for each main file.')
    
    return file_matches

def main(args):
    directory = args.directory
    second_directory = args.second_directory
    force_language_prompt = args.force_language_prompt
    ask_for_additional_flags = args.prompt_additional_tags
    subtitles_delay = args.delay_subtitles

    # mkv_files_to_modify = get_matching_files_from_directory(directory)
    main_files = get_matching_files_from_directory(directory)
    file_matches = get_tracks_to_mux(main_files)
    attachments = get_font_attachments(directory)

    if second_directory:
        file_matches = add_matches_from_second_directory(file_matches, second_directory)

    mux_files_into_mkv(file_matches, attachments=attachments, force_language_prompt=force_language_prompt, ask_for_additional_flags=ask_for_additional_flags, subtitles_delay=subtitles_delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvrearrange', description="Rearrange and set the flags of the tracks in all the similar MKV files in the directory.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    parser.add_argument('-d2', '--second-directory', default=None, help='Directory of numbered MKV files to merge')
    parser.add_argument('-l', '--force-language-prompt', action='store_true', help='Forces the program to prompt the user to input languages for each track.')
    parser.add_argument('-a', '--prompt-additional-tags', action='store_true', help='Forces the program to prompt the user to input all optional tags for each track.')
    parser.add_argument('-d', '--delay-subtitles', default=0, type=int, help='Delay the subtitles by the given number of milliseconds.')
    
    args = parser.parse_args()
    main(args)
