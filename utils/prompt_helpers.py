from utils.file_management_helpers import *

def prompt_for_flag(valid_ids, enforce_flag=False, flag_is_exclusive=False, flag_description='flagged'):
    """Prompt the user to give the IDs of tracks that should be flagged."""
    if enforce_flag and len(valid_ids) == 1:
        flag_ids = [valid_ids[0]]
    else:
        print(
            f'Enter the ID of the track{"s" if not flag_is_exclusive else ""} (int:int){", if any," if not enforce_flag else ""} that should be {flag_description}{", separated by commas" if not flag_is_exclusive else ""}: '
        )
        # Loop until valid input is given.
        while True:
            try:
                flag_ids = input().strip().split(',')
                flag_ids = [id.strip() for id in flag_ids if id]
                if len(flag_ids) >= 1 and not flag_is_exclusive:
                    for id in flag_ids:
                        if not bool(global_id_pattern.match(id)):
                            print(f"The ID provided, {id}, is not of the form int:int. Try again: ")
                            raise ValueError
                        if id not in valid_ids:
                            print(f'The ID provided, {id}, is not one of the present IDs. Try again: ')
                            raise ValueError
                elif flag_is_exclusive and len(flag_ids) > 1:
                    print(f'You may only choose one track to be {flag_description}.')
                    raise ValueError
                elif enforce_flag and len(flag_ids) < 1:
                    print(f'You must choose a track to be {flag_description}.')
                    raise ValueError
                else:
                    flag_ids = []
                break
            except ValueError:
                continue
    return flag_ids

def prompt_for_tracks_flags(tracks_info, enforce_default=True, ask_for_forced=False, ask_for_additional_audio_flags=False, ask_for_additional_subtitles_flags=False):
    """Ask the user which of the given tracks should have certain flags."""
    if not tracks_info: return []

    # Keep the IDs of all the tracks in a list
    present_global_ids = [f'{track["file_id"]}:{track["id"]}' for track in tracks_info]

    # Initialize lists of ids
    default_ids = []
    forced_ids = []
    flag_original_ids = []
    visual_impaired_ids = []
    commentary_ids = []
    hearing_impaired_ids = []
    text_description_ids = []

    # DEFAULT FLAG
    default_ids = prompt_for_flag(present_global_ids, enforce_flag=enforce_default, flag_is_exclusive=True, flag_description="DEFAULT")

    # FORCED FLAG
    # Prompt the user to determine which track if any should be set as forced
    if ask_for_forced:
        forced_ids = prompt_for_flag(present_global_ids, flag_is_exclusive=False, flag_description="FORCED")

    # AUDIO FLAGS
    # Prompt the user to determine which audio tracks should be audio description, original language, or commentary
    if ask_for_additional_audio_flags:
        flag_original_ids = prompt_for_flag(present_global_ids, flag_description="marked as being in the ORIGINAL LANGUAGE")
        visual_impaired_ids = prompt_for_flag(present_global_ids, flag_description="marked as being AUDIO DESCRIPTION")
        commentary_ids = prompt_for_flag(present_global_ids, flag_description="marked as being COMMENTARY TRACKS")

    # SUBTITLES FLAGS
    # Prompt the user to determine which subtitles tracks should be for the hearing impaired, original language, or commentary
    if ask_for_additional_subtitles_flags:
        flag_original_ids = prompt_for_flag(present_global_ids, flag_description="marked as being in the ORIGINAL LANGUAGE")
        hearing_impaired_ids = prompt_for_flag(present_global_ids, flag_description="marked as for the DEAF AND HARD OF HEARING (a.k.a. SDH or CC)")
        text_description_ids = prompt_for_flag(present_global_ids, flag_description="marked as containing TEXT DESCRIPTION of on-screen content")
        
    # Set flags
    for track in tracks_info:
        track['default_track'] = bool(f'{track["file_id"]}:{track["id"]}' in default_ids)
        track['forced_track'] = bool(f'{track["file_id"]}:{track["id"]}' in forced_ids)
        track['flag_original'] = bool(f'{track["file_id"]}:{track["id"]}' in flag_original_ids)
        track['flag_visual_impaired'] = bool(f'{track["file_id"]}:{track["id"]}' in visual_impaired_ids)
        track['flag_commentary'] = bool(f'{track["file_id"]}:{track["id"]}' in commentary_ids)
        track['flag_hearing_impaired'] = bool(f'{track["file_id"]}:{track["id"]}' in hearing_impaired_ids)
        track['flag_text_descriptions'] = bool(f'{track["file_id"]}:{track["id"]}' in text_description_ids)

    return tracks_info

def prompt_for_tracks_names(tracks_info):
    """Ask the user to give names to each track."""
    for track in tracks_info:
        list_tracks([track])
        new_name = input("Input a new NAME for the above track (press enter to skip): ").strip()
        if new_name:
            track['track_name'] = new_name
    return tracks_info

def prompt_for_tracks_languages(tracks_info, force_language_prompt=False):
    """Ask the user to give languages tracks."""
    for track in tracks_info:
        if force_language_prompt or track['language'] == 'und':
            while True:
                list_tracks([track])
                language = input("Input a LANGUAGE for the above track (press enter to skip): ").strip()
                if language == '':
                    break
                elif is_valid_language_code(language):
                    track['language'] = language
                    break
                else:
                    print("Please input a valid 3-letter language code (e.g. 'eng' or 'jpn').")
                    continue
    return tracks_info