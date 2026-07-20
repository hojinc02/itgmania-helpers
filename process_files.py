import sys
import os
import subprocess
import shutil
import platform
import re
from pathlib import Path

from constants import TOMLtype
from typing import Callable, Optional, Any
from util import read_file

def format_path(path: Path, mode: Optional[str] = None) -> Path: 
    if mode is None: 
        return path
    else: 
        return Path(str(path).format(mode = mode))

def recursive_mod(dir: Path, action_file: str, action_dict: TOMLtype, 
                action: Callable, mode: Optional[str] = None, level: int = 1) -> None: 
    for filepath in dir.iterdir(): 
        if filepath.is_dir(): 
            if level <= 0: 
                continue
            recursive_mod(filepath, action_file, action_dict, action, mode, level - 1)
        elif filepath.samefile(dir / action_file): 
            action(filepath, action_dict, mode)

def edit_settings(path: Path, settings_dict: TOMLtype, mode: Optional[str] = None) -> None: 
    assert path.exists(), f'{path} not found'
    if mode is not None: 
        settings_dict = settings_dict[mode]
    lines = read_file(path)
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

def replace_file(path: Path, replacement_dict: TOMLtype, mode: Optional[str] = None) -> None: 
    assert path.exists(), f'{path} not found'
    replace_path = Path(replacement_dict['replacement_path'])
    replace_path = format_path(replace_path, mode)
    shutil.copy(replace_path, path)

def link_folder(sympath: Path, link_dict: TOMLtype, mode: Optional[str] = None) -> None: 
    if sympath.exists():
        try:
            if sys.platform == 'win32':
                os.rmdir(sympath) 
            else:
                os.remove(sympath)
        except OSError as e:
            print(f'WARNING: could not remove {sympath!r}: {e}')
    target_path = Path(link_dict['target_path'])
    target_path = format_path(target_path, mode)
    
    if sys.platform == 'win32': 
        result = subprocess.run([
            'powershell', 
            '-Command', 
            rf'New-Item -ItemType Junction -Path {sympath} -Target {target_path}'
        ], capture_output=True)
        if result.returncode != 0: 
            print(result.stderr.decode())
    else: 
        os.symlink(target_path, sympath)

def matchreplace(path: Path, match_dict: TOMLtype, mode: Optional[str] = None) -> None: 
    assert path.exists(), f'{path} not found'
    if mode is not None: 
        match_dict = match_dict[mode]
    
    content = ''.join(read_file(path))
    
    for m in match_dict['list']: 
        result = re.search(m['match'], content)
        if result is None:
            print(f"WARNING: no match for pattern {m['match']!r} in {path}", flush=True)
            continue
        content = content[:result.start()] + m['replace'] \
                    + content[result.end():]
    
    with open(path, 'w') as f: 
        f.write(content)

ACTIONS: dict[str, Callable] = {
    'settings': edit_settings, 
    'replacement': replace_file, 
    'link': link_folder, 
    'matchreplace': matchreplace
}

def get_action_str(mod: str) -> str: 
    assert sum([(1 if action in mod else 0) for action in ACTIONS]) == 1, \
        f'Error: {mod} has zero or multiple possible actions'
    for action_str in ACTIONS: 
        if action_str in mod: 
            return action_str
    print('Error: get_action_dict should not be here')
    return 'Error'

def process_files(config: dict[str, Any], mode: str) -> None: 
    for mod_dict in config['files']: 
        action_str = get_action_str(mod_dict)
        action = ACTIONS[action_str]
        action_mode = mode if mod_dict.get('mode_required', False) else None
        
        path = mod_dict['path']
        
        if 'dir' in mod_dict: 
            dir_path = Path(mod_dict['dir'])
            recursive_mod(dir_path, path, 
                          mod_dict[action_str], action, action_mode)
        else: 
            path = Path(path)
            action(path, mod_dict[action_str], action_mode)