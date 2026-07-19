from pathlib import Path
from typing import Optional
import sys

def read_file(path: Path) -> list[str]: 
    with open(path, 'r') as f: 
        lines = f.readlines()
    return lines

def getch() -> str: 
    if sys.platform == 'win32': 
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