import os
import argparse
import subprocess
import re
from utils.file_management_helpers import *

def main(args):
    directory = args.directory
    
    mkv_files = get_video_files_from_directory(directory)

    print(f'Checking the integrity of {len(mkv_files)} file(s).')
    invalid_files = []
    for file_path in mkv_files:
        command = f'mkvalidator --no-warn --quick "{file_path}"'
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=30)
            output = result.stdout

            # Ensures the command returned with no errors
            if "the file appears to be valid" not in output:
                invalid_files.append(file_path)
                print(f'Could not validate "{os.path.basename(file_path)}"')
                cleaned_output = re.sub(r'\.{2,}', '', output).strip()
                print(cleaned_output)
            else:
                print(f'Validated "{os.path.basename(file_path)}"')

        except subprocess.TimeoutExpired:
            print(f'Timeout while processing file "{os.path.basename(file_path)}"')
            invalid_files.append(file_path)

    if invalid_files:
        print("\n\n*** Invalid files detected: ***\n")
        for invalid_file in invalid_files:
            print(invalid_file)
        print()
    else:
        print("\n\nAll files are valid.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog='mkvverify', description="Use mkvalidator to check all the MKV files in a directory.")
    parser.add_argument('directory', nargs='?', default=os.getcwd(), help='Directory to process')
    
    args = parser.parse_args()
    main(args)
