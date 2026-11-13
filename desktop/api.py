"""Everything the interface can do. Plain Python, no GUI imports, fully unit-testable.

Every public method returns {'ok': True, 'data': ...} or {'ok': False, 'error': '...'}.
"""
import functools
import hashlib
import subprocess
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

import detect
import updater
from catalog import PLAYERS, preset
from core import decode_link, game_cfg_dir, install_cfg, launch_args, validate_cfg
from preferences import parse_games, serialize_games
from release_config import REPOSITORY, SITE_URL, VERSION

TRUSTED_HOSTS = {'prosettings.net', 'github.com', urllib.parse.urlsplit(SITE_URL).hostname}
MAX_FILE = 262144


def safe(fn):
    @functools.wraps(fn)
    def wrapper(self, *args, **kwargs):
        try:
            return {'ok': True, 'data': fn(self, *args, **kwargs)}
        except Exception as error:  # reported to the interface, never silently dropped
            return {'ok': False, 'error': str(error) or error.__class__.__name__}
    return wrapper


def read_cfg(path):
    file = Path(path)
    if not file.is_file() or file.suffix.lower() != '.cfg' or file.stat().st_size > MAX_FILE:
        raise ValueError('Choose a .cfg file up to 256 KB.')
    return validate_cfg(file.read_text(encoding='utf-8-sig'))


class Api:
    def __init__(self, store, dialog=None, popen=subprocess.Popen, opener=webbrowser.open, register=None):
        self._s = store
        self._dialog = dialog or (lambda kind, **kwargs: None)
        self._popen = popen
        self._open = opener
        self._register = register
        self._available = None
        self._lock = threading.Lock()
        self._notice = None
        self._quit = lambda: None

    # ---- hooks used by main.py (underscore = not exposed to the page)
    def _set_notice(self, text, goto=None):
        self._notice = dict(text=text, goto=goto)

    def _set_quit(self, fn):
        self._quit = fn

    # ---- state and preferences
    @safe
    def state(self):
        get = self._s.get
        notice, self._notice = self._notice, None
        return dict(version=VERSION, site=SITE_URL, windows=sys.platform == 'win32',
                    games=parse_games(get('interests')), intro_complete=get('intro_complete') == '1',
                    game=get('game'), steam=get('steam'), reduce_motion=get('reduce_motion') == '1',
                    update_repo=get('update_repo') or REPOSITORY, update_auto=get('update_auto') != '0',
                    nickname=get('nickname'), notice=notice)

    @safe
    def set_games(self, games):
        value = serialize_games(games)
        self._s.put('interests', value)
        self._s.put('intro_complete', '1')
        return parse_games(value)

    @safe
    def set_motion(self, reduced):
        self._s.put('reduce_motion', '1' if reduced else '0')
        return bool(reduced)

    @safe
    def open_url(self, url):
        parts = urllib.parse.urlsplit(str(url))
        if parts.scheme != 'https' or parts.hostname not in TRUSTED_HOSTS:
            raise ValueError('This link is not allowed.')
        self._open(url)
        return True

    # ---- pro players
    @safe
    def players(self):
        return [dict(p, edpi=round(p['dpi'] * p['sens']), preset=preset(p)) for p in PLAYERS]

    @safe
    def save_player(self, player_id):
        player = next((p for p in PLAYERS if p['id'] == player_id), None)
        if not player:
            raise ValueError('Unknown player.')
        return self._s.add_unique(player['name'], preset(player))

    # ---- library
    def _signature(self):
        rows = self._s.configs()
        return hashlib.sha1(repr([(r[0], r[1], len(r[2])) for r in rows]).encode()).hexdigest()

    @safe
    def library(self):
        rows = self._s.configs()
        return dict(sig=self._signature(), items=[dict(id=r[0], name=r[1], size=len(r[2].encode('utf-8'))) for r in rows])

    @safe
    def library_sig(self):
        return self._signature()

    @safe
    def get_config(self, ident):
        row = self._s.config(ident)
        return dict(id=row[0], name=row[1], content=row[2], size=len(row[2].encode('utf-8')))

    @safe
    def import_file(self):
        path = self._dialog('open', types=('Config CS2 (*.cfg)',))
        if not path:
            return None
        return dict(id=self._s.add_config(Path(path).stem, read_cfg(path)), name=Path(path).stem)

    @safe
    def pick_cfg(self):
        path = self._dialog('open', types=('Config CS2 (*.cfg)',))
        return dict(name=Path(path).stem, content=read_cfg(path)) if path else None

    @safe
    def save_config(self, ident, name, content):
        name = str(name).strip()
        if not name or len(name) > 120:
            raise ValueError('Use a name between 1 and 120 characters.')
        self._s.config(ident)
        self._s.update_config(ident, name, validate_cfg(content))
        return True

    @safe
    def delete_config(self, ident):
        self._s.delete_config(ident)
        return True

    @safe
    def export_config(self, ident):
        row = self._s.config(ident)
        path = self._dialog('save', filename='settingscs2_export.cfg', types=('Config CS2 (*.cfg)',))
        if not path:
            return None
        Path(path).write_text(row[2], encoding='utf-8')
        return str(path)

    @safe
    def apply_config(self, ident, launch=False):
        row = self._s.config(ident)
        game, steam = self._s.get('game'), self._s.get('steam')
        if not game:
            raise ValueError('Choose your CS2 folder in Settings first.')
        if launch and not steam:
            raise ValueError('Choose Steam.exe in Settings to launch the game.')
        args = launch_args(steam, 'settingscs2_' + row[0] + '.cfg') if launch else None
        target, backup = install_cfg(game, row[0], row[2])
        if args:
            self._popen(args, shell=False)
        return dict(target=target.name, backup=bool(backup), launched=bool(args))

    @safe
    def handle_link(self, uri):
        name, content = decode_link(uri)
        return dict(id=self._s.add_config(name, content), name=name)

    # ---- community (local only)
    @safe
    def community(self):
        return self._s.community()

    @safe
    def community_add(self, data):
        fields = {k: str(data.get(k, '')).strip() for k in ('name', 'author', 'mouse', 'keyboard', 'description')}
        if not fields['name'] or not fields['author']:
            raise ValueError('Enter a config name and nickname.')
        if any(len(v) > 240 for v in fields.values()):
            raise ValueError('Use up to 240 characters per field.')
        content = validate_cfg(data.get('content'))
        name = fields.pop('name')[:120]
        self._s.put('nickname', fields['author'])
        return self._s.add_community(name, content, fields)

    @safe
    def community_delete(self, ident):
        self._s.delete_community(ident)
        return True

    @safe
    def community_to_library(self, ident):
        row = next((c for c in self._s.community() if c['id'] == ident), None)
        if not row:
            raise ValueError('This setup no longer exists.')
        return self._s.add_unique(row['name'], row['content'])

    # ---- paths and protocol
    @safe
    def pick_folder(self):
        return self._dialog('folder')

    @safe
    def pick_steam(self):
        return self._dialog('open', types=('Steam (*.exe)',))

    @safe
    def detect_paths(self):
        return detect.detect()

    @safe
    def save_paths(self, game, steam):
        game, steam = str(game).strip(), str(steam).strip()
        game_cfg_dir(game)
        if steam:
            launch_args(steam, 'settingscs2_' + '0' * 32 + '.cfg')
        self._s.put('game', game)
        self._s.put('steam', steam)
        return True

    @safe
    def register_protocol(self):
        if not self._register:
            raise ValueError('Add to app is available on Windows only.')
        self._register()
        return True

    # ---- updates
    @safe
    def save_update_settings(self, repo, auto):
        value = updater.repository(repo)
        self._s.put('update_repo', value)
        self._s.put('update_auto', '1' if auto else '0')
        self._available = None
        return value

    @safe
    def check_update(self):
        repo = updater.repository(self._s.get('update_repo') or REPOSITORY)
        self._available = updater.latest(repo, VERSION)
        return self._available and dict(version=self._available['version'], repo=self._available['repo'])

    @safe
    def install_update(self):
        if not self._available:
            raise ValueError('Check for updates first.')
        if sys.platform != 'win32':
            raise ValueError('The installer requires Windows.')
        if not self._lock.acquire(blocking=False):
            raise ValueError('An update is already in progress.')
        try:
            installer = updater.download(dict(self._available), self._s.base / 'updates')
            self._popen([str(installer), '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART',
                         '/LOG=' + str(self._s.base / 'update-install.log')], shell=False)
        finally:
            self._lock.release()
        self._quit()
        return True
