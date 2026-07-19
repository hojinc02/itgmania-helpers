import sys
import tomllib
import subprocess

from constants import CONFIG_PATH
from util import read_file, getch
from process_files import process_files

def main() -> None:
    with open(CONFIG_PATH, 'rb') as f: 
        config = tomllib.load(f)

    # Receive key input for mode selection
    kkey_dict = config['mode_keys']
    print('Press a key to launch')
    for kkey, mode in kkey_dict.items(): 
        print(f'{mode}: <{kkey}>')
    while True: 
        kkey = getch()
        if kkey in kkey_dict.keys(): 
            if kkey_dict[kkey] == '__exit': 
                print('Exit')
                return
            else: 
                mode = kkey_dict[kkey]
                break

    process_files(config, mode)
    
    # start game
    gamepath = config['GamePath']['path']
    if sys.platform == 'win32': 
        subprocess.Popen([gamepath])
    elif sys.platform == 'darwin': 
        subprocess.Popen(['open', gamepath])
    elif sys.platform == 'linux': 
        subprocess.Popen([gamepath])
    else: 
        print(f'Detected non-standard os: {sys.platform}. Report to github for handling. ')
        subprocess.Popen([gamepath])
    
if __name__ == '__main__': 
    try: 
        main()
    except Exception: 
        import traceback, sys
        traceback.print_exc()
        input("\nSomething went wrong. Press Enter to close.")
        sys.exit(1)