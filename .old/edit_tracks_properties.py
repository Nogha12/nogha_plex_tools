import os
import argparse
import subprocess
from utils.file_management_helpers import *
from utils.prompt_helpers import *

def prompt_for_new_tracks_info(tracks_info, force_language_prompt=False, ask_for_additional_flags=False):
    """Ask the user to give flags, names, and languages to each type of track."""
    # Split the tracks_info into video, audio, subtitles, and other
    video_tracks_info = [track for track in tracks_info if track['type'] == 'video']
    audio_tracks_info = [track for track in tracks_info if track['type'] == 'audio']
    subtitles_tracks_info = [track for track in tracks_info if track['type'] == 'subtitles']
    other_tracks_info = [track for track in tracks_info if track['type'] not in ['video', 'audio', 'subtitles']]
    
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
    audio_tracks_info = prompt_for_tracks_flags(audio_tracks_info, enforce_default=True, ask_for_additional_audio_flags=ask_for_additional_flags)
    audio_tracks_info = prompt_for_tracks_languages(audio_tracks_info, force_language_prompt=force_language_prompt)
    audio_tracks_info = prompt_for_tracks_names(audio_tracks_info)

    # SUBTITLES TRACKS
    # Prompt for subtitles order and default/forced track
    if subtitles_tracks_info:
        print("\nSubtitles tracks:")
        list_tracks(subtitles_tracks_info)
        subtitles_tracks_info = prompt_for_tracks_flags(subtitles_tracks_info, enforce_default=False, ask_for_forced=True, ask_for_additional_subtitles_flags=ask_for_additional_flags)
        subtitles_tracks_info = prompt_for_tracks_languages(subtitles_tracks_info, force_language_prompt=force_language_prompt)
        subtitles_tracks_info = prompt_for_tracks_names(subtitles_tracks_info)

    updated_tracks_info = video_tracks_info + audio_tracks_info + subtitles_tracks_info + other_tracks_info

    return updated_tracks_info

def update_track_properties(file_path, tracks_info, set_additional_flags=False):
    """Update the default and forced properties of the tracks using mkvpropedit."""
    additional_flags_names = [
        'flag_original',
        'flag_hearing_impaired',
        'flag_visual_impaired',
        'flag_text_descriptions',
        'flag_commentary'
    ]

    for track in tracks_info:
        track_number = track['number']
        default_flag = '1' if track['default_track'] else '0'
        forced_flag = '1' if track['forced_track'] else '0'
        language = track['language']

        # Create the command to run
        command = f'mkvpropedit "{file_path}" --edit track:{track_number} --set flag-default={default_flag} --set flag-forced={forced_flag} --set language="{language}"'

        # Add the name tag if present
        track_name = track['track_name']
        if track_name and track_name != 'N/A':
            command += f' --set name="{track_name}"'

        # Add additional flags to the command if present
        if set_additional_flags:
            for flag_name in additional_flags_names:
                flag = '1' if track[flag_name] else '0'
                header_name = re.sub('_', '-', flag_name).strip()
                command += f' --set {header_name}={flag}'

        subprocess.run(command, shell=True)

def edit_mkv_tracks_properties(file_paths, force_language_prompt=False, ask_for_additional_flags=False):
    """Prompt the user to set the tages of the example track, and set the tags for all files."""
    # Get the first track's info to use as a template
    first_tracks_info = get_tracks_info(file_paths[0])
    
    # Prompt the user to give the new order and default/forced status for the tracks
    tracks_template = prompt_for_new_tracks_info(first_tracks_info, force_language_prompt=force_language_prompt, ask_for_additional_flags=ask_for_additional_flags)
    
    print("\nUsing the following template to update tracks info in all .mkv files:")
    for track in tracks_template:
        print(track)

    user_input = input("Go ahead with editing all the tracks to this format? (type 'y' or 'yes'): ").strip().lower()
    if user_input not in ['y', 'yes']:
        print("Aborting. . .")
        return

    for file_path in file_paths:
        # Update track properties
        update_track_properties(file_path, tracks_template, set_additional_flags=ask_for_additional_flags)

    print("Finished editing files.")

def main(args):
    directory = args.directory
    force_language_prompt = args.force_language_prompt
    ask_for_additional_flags = args.prompt_additional_tags

    mkv_files_to_modify = get_matching_files_from_directory(directory)
    edit_mkv_tracks_properties(mkv_files_to_modify, force_language_prompt=force_language_prompt, ask_for_additional_flags=ask_for_additional_flags)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvrearrange', description="Rearrange and set the flags of the tracks in all the similar MKV files in the directory.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    parser.add_argument('-l', '--force-language-prompt', action='store_true', help='Forces the program to prompt the user to input languages for each track.')
    parser.add_argument('-a', '--prompt-additional-tags', action='store_true', help='Forces the program to prompt the user to input all optional tags for each track.')
    
    args = parser.parse_args()
    main(args)
