"""File-only operations. Does not execute config contents in the operating system."""
import base64
import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone

MAX_SIZE = 262144

def validate_cfg(text):
    if not isinstance(text, str) or not text.strip() or '\0' in text:
        raise ValueError('The config must contain text with no NUL characters.')
    if len(text.encode('utf-8')) > MAX_SIZE:
        raise ValueError('The config exceeds 256 KB.')
    return text

def decode_link(uri):
    prefix = 'settingscs2://import/'
    if not uri.startswith(prefix) or len(uri) > 8192:
        raise ValueError('Invalid or oversized import link.')
    data = uri[len(prefix):].rstrip('/')
    if not re.fullmatch(r'[A-Za-z0-9_-]+', data):
        raise ValueError('Invalid import link.')
    payload = json.loads(base64.urlsafe_b64decode(data + '=' * (-len(data) % 4)))
    if not isinstance(payload, dict) or not isinstance(payload.get('name'), str):
        raise ValueError('Invalid import format.')
    name = payload['name'].strip()
    if not 1 <= len(name) <= 120:
        raise ValueError('Invalid config name.')
    return name, validate_cfg(payload.get('cfg'))

def game_cfg_dir(root):
    root = Path(root).resolve()
    cfg_dir = root / 'game' / 'csgo' / 'cfg'
    if not (root / 'game' / 'bin' / 'win64' / 'cs2.exe').is_file() or not cfg_dir.is_dir():
        raise ValueError('Choose the Counter-Strike Global Offensive folder containing game/bin/win64/cs2.exe and game/csgo/cfg.')
    if cfg_dir.is_symlink() or not cfg_dir.resolve().is_relative_to(root):
        raise ValueError('The cfg folder must not redirect outside the game folder.')
    return cfg_dir

def install_cfg(root, config_id, text):
    validate_cfg(text)
    if not re.fullmatch(r'[a-f0-9]{32}', config_id):
        raise ValueError('Invalid ID.')
    cfg_dir = game_cfg_dir(root)
    target = cfg_dir / ('settingscs2_' + config_id + '.cfg')
    if target.is_symlink():
        raise ValueError('The target file cannot be a link.')
    backup = None
    if target.exists():
        backup = target.with_suffix('.cfg.' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f') + '.bak')
        backup.write_bytes(target.read_bytes())
    temporary = cfg_dir / ('.settingscs2_' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(text, encoding='utf-8')
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)
    return target, backup

def launch_args(steam_path, filename):
    if not re.fullmatch(r'settingscs2_[a-f0-9]{32}\.cfg', filename):
        raise ValueError('Invalid exec filename.')
    steam = Path(steam_path)
    if steam.name.lower() != 'steam.exe' or not steam.is_file():
        raise ValueError('Select Steam.exe.')
    return [str(steam), '-applaunch', '730', '+exec', filename]

