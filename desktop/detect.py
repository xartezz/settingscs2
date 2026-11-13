"""Find Steam and Counter-Strike 2 without asking the user to browse folders."""
import re
import sys
from pathlib import Path

GAME_DIR = 'Counter-Strike Global Offensive'


def steam_root():
    if sys.platform != 'win32':
        return None
    import winreg
    for hive, sub, name in ((winreg.HKEY_CURRENT_USER, r'Software\Valve\Steam', 'SteamPath'),
                            (winreg.HKEY_LOCAL_MACHINE, r'SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath')):
        try:
            with winreg.OpenKey(hive, sub) as key:
                return Path(winreg.QueryValueEx(key, name)[0])
        except OSError:
            continue
    return None


def libraries(root):
    found = [Path(root)]
    vdf = Path(root) / 'steamapps' / 'libraryfolders.vdf'
    try:
        text = vdf.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return found
    for raw in re.findall(r'"path"\s+"([^"]+)"', text):
        path = Path(raw.replace('\\\\', '\\'))
        if path not in found:
            found.append(path)
    return found


def detect(root=None):
    root = Path(root) if root else steam_root()
    result = {'steam': '', 'game': ''}
    if not root:
        return result
    exe = root / 'steam.exe'
    if exe.is_file():
        result['steam'] = str(exe)
    for library in libraries(root):
        game = library / 'steamapps' / 'common' / GAME_DIR
        if (game / 'game' / 'bin' / 'win64' / 'cs2.exe').is_file():
            result['game'] = str(game)
            break
    return result
