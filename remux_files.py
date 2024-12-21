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

def mux_files(file_paths, tracks_info, output_path, attachments=[]):
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

def mux_files_into_mkv(file_matches, attachments=[], force_language_prompt=False, ask_for_additional_flags=False):
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
            if file_path.lower().endswith('.mkv'):
                mkv_file_path = file_path
                break # break here because the primary MKV should be listed first
        new_dir = os.path.join(os.path.dirname(mkv_file_path), 'remux')
        os.makedirs(new_dir, exist_ok=True)
        output_path = os.path.join(new_dir, os.path.basename(mkv_file_path))
        
        # Check if reordering is needed and remux
        if get_identifying_info_from_tracks_info(tracks_template) != get_identifying_info_from_tracks_info(get_tracks_info(file_paths[0])):
            mux_files(file_paths, tracks_template, output_path, attachments=attachments)
        else:
            # If no reordering is needed, just copy the file
            copyfile(file_paths[0], output_path)

        # Update track properties
        update_track_properties(output_path, tracks_template, set_additional_flags=ask_for_additional_flags)

    print("Finished remuxing files.")

def get_matching_tracks_mkvs(mkv_files):
    """Return a list of lists of files with the same base name."""
    file_matches = []
    for mkv_file in mkv_files:
        directory = os.path.dirname(mkv_file)
        match_name = os.path.basename(mkv_file)
        match_name = os.path.splitext(match_name)[0].split('.')[0]
        match_name = re.sub(r'\[.*?\]', '', match_name).strip()
        matching_files = []
        for other_file in os.listdir(directory):
            file_match_name = os.path.basename(other_file)
            spit_filename = os.path.splitext(file_match_name)
            file_extension = spit_filename[1]
            file_match_name = spit_filename[0].split('.')[0]
            file_match_name = re.sub(r'\[.*?\]', '', file_match_name).strip()
            if is_muxable_extension(file_extension) and file_match_name == match_name:
                matching_files.append(os.path.join(directory, other_file))
        file_matches.append(matching_files)
    return file_matches

def main(args):
    directory = args.directory
    second_directory = args.second_directory
    force_language_prompt = args.force_language_prompt
    ask_for_additional_flags = args.prompt_additional_tags

    mkv_files_to_modify = get_matching_files_from_directory(directory)
    file_matches = get_matching_tracks_mkvs(mkv_files_to_modify)
    attachments = get_font_attachments(directory)

    if second_directory:
        file_matches = add_matches_from_second_directory(file_matches, second_directory)

    mux_files_into_mkv(file_matches, attachments=attachments, force_language_prompt=force_language_prompt, ask_for_additional_flags=ask_for_additional_flags)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvrearrange', description="Rearrange and set the flags of the tracks in all the similar MKV files in the directory.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    parser.add_argument('-d2', '--second-directory', default=None, help='Directory of numbered MKV files to merge')
    parser.add_argument('-l', '--force-language-prompt', action='store_true', help='Forces the program to prompt the user to input languages for each track.')
    parser.add_argument('-a', '--prompt-additional-tags', action='store_true', help='Forces the program to prompt the user to input all optional tags for each track.')
    
    args = parser.parse_args()
    main(args)
