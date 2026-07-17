import subprocess
import os
import shutil
import tomllib
import platform
import sys
import re


# Put the absolute full config.toml path here
config_path = r"C:\Users\Hojin\Documents\StepmaniaAssets\itgmania-helpers\config.toml"


system = platform.system()

def read_file(path, until=None): 
    lines = []
    with open(path, 'r') as f: 
        if until is not None: 
            for line in f: 
                lines.append(line)
                if line.strip() == until: 
                    break
        else: 
            lines = f.readlines()
    return lines

def getch(): 
    if system == 'Windows': 
        import msvcrt
        return msvcrt.getwch()
    else: 
        import tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try: 
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally: 
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

def recursive_mod(dir, action_path, action_dict, action, mode = None): 
    for filepath in os.listdir(dir): 
        subpath = os.path.join(dir, filepath)
        if os.path.isdir(subpath): 
            recursive_mod(subpath, action_path, action_dict, action, mode)
        elif filepath == action_path: 
            action(subpath, action_dict, mode)

def edit_settings(path, settings_dict, mode = None): 
    assert os.path.exists(path), f'{path} not found'
    if mode is not None: 
        settings_dict = settings_dict[mode]
    lines = read_file(path, settings_dict.get('until'))
    with open(path, 'w') as f:
        for line in lines:
            found = False
            for key, val in settings_dict.items(): 
                if line.strip().startswith(key): 
                    f.write(f'{key}={val}\n')
                    found = True
                    break
            if not found:
                f.write(line)

def replace_file(path, replacement_dict, mode = None): 
    assert os.path.exists(path), f'{path} not found'
    replace_path = replacement_dict['replacement_path']
    if mode is not None: 
        replace_path = replace_path.format(mode = mode)
    shutil.copy(replace_path, path)

def link_folder(sympath, link_dict, mode = None): 
    if os.path.exists(sympath): 
        os.remove(sympath)
    target_path = link_dict['target_path']
    if mode is not None: 
        target_path = target_path.format(mode = mode)
    
    if system == 'Windows': 
        result = subprocess.run([
            'powershell', 
            '-Command', 
            rf'New-Item -ItemType Junction -Path {sympath} -Target {target_path}'
        ], capture_output=True)
        if result.returncode != 0: 
            print(result.stderr.decode())
    else: 
        os.symlink(target_path, sympath)

def matchreplace(path, match_dict, mode = None): 
    assert os.path.exists(path), f'{path} not found'
    if mode is not None: 
        match_dict = match_dict[mode]
    
    content = ''.join(read_file(path, match_dict.get('until')))
    
    for m in match_dict['list']: 
        result = re.search(m['match'], content)
        if result is None:
            print(f"WARNING: no match for pattern {m['match']!r} in {path}", flush=True)
            continue
        content = content[:result.start()] + m['replace'] \
                    + content[result.end():]
    
    with open(path, 'w') as f: 
        f.write(content)

actions = {
    'settings': edit_settings, 
    'replacement': replace_file, 
    'link': link_folder, 
    'matchreplace': matchreplace
}

def get_action_str(mod): 
    assert sum([(1 if action in mod else 0) for action in actions]) == 1, \
        f'Error: {mod} has zero or multiple possible actions'
    for action_str in actions: 
        if action_str in mod: 
            return action_str
    print('Error: get_action_dict should not be here')
    
def main():
    # Load config from toml
    with open(config_path, 'rb') as f: 
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

    # Process files to modify
    for mod_dict in config['files']: 
        action_str = get_action_str(mod_dict)
        action = actions[action_str]
        action_mode = mode if mod_dict.get('mode_required', False) else None
        if 'dir' in mod_dict: 
            recursive_mod(mod_dict['dir'], mod_dict['path'], 
                          mod_dict[action_str], action, action_mode)
        else: 
            action(mod_dict['path'], mod_dict[action_str], action_mode)
    
    # start game
    gamepath = config['GamePath']['path']
    if system == 'Windows': 
        subprocess.Popen([gamepath])
    elif system == 'Darwin': 
        subprocess.Popen(['open', gamepath])
    else: 
        subprocess.Popen([gamepath])
    
if __name__ == '__main__': 
    try: 
        main()
    except Exception: 
        import traceback
        traceback.print_exc()
        input("\nSomething went wrong. Press Enter to close.")
        sys.exit(1)