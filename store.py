"""SQLite library. Same location and schema as earlier versions, so existing data is kept."""
import json
import os
import sqlite3
import threading
import uuid
from pathlib import Path
from core import validate_cfg


def default_base():
    return Path(os.getenv('LOCALAPPDATA', str(Path.home()))) / 'SettingsCS2'


class Store:
    def __init__(self, base=None):
        self.base = Path(base) if base else default_base()
        self.base.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.db = sqlite3.connect(self.base / 'library.sqlite3', check_same_thread=False, timeout=10)
        with self.lock:
            self.db.execute('CREATE TABLE IF NOT EXISTS configs (id TEXT PRIMARY KEY, name TEXT NOT NULL, content TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)')
            self.db.execute('CREATE TABLE IF NOT EXISTS community (id TEXT PRIMARY KEY, name TEXT NOT NULL, content TEXT NOT NULL, metadata TEXT NOT NULL)')
            self.db.commit()

    def close(self):
        with self.lock:
            self.db.close()

    def _run(self, sql, args=(), write=False, one=False):
        with self.lock:
            cursor = self.db.execute(sql, args)
            if write:
                self.db.commit()
            return (cursor.fetchone() if one else cursor.fetchall()) if not write else None

    def get(self, key):
        row = self._run('SELECT value FROM settings WHERE key=?', (key,), one=True)
        return row[0] if row else ''

    def put(self, key, value):
        self._run('INSERT OR REPLACE INTO settings VALUES (?,?)', (key, value), write=True)

    def add_config(self, name, content):
        validate_cfg(content)
        ident = uuid.uuid4().hex
        self._run('INSERT INTO configs VALUES (?,?,?)', (ident, name[:120], content), write=True)
        return ident

    def add_unique(self, name, content):
        row = self._run('SELECT id FROM configs WHERE name=? AND content=?', (name, content), one=True)
        return row[0] if row else self.add_config(name, content)

    def configs(self):
        return self._run('SELECT id,name,content FROM configs ORDER BY rowid DESC')

    def config(self, ident):
        row = self._run('SELECT id,name,content FROM configs WHERE id=?', (ident,), one=True)
        if not row:
            raise ValueError('This config is no longer in your library.')
        return row

    def update_config(self, ident, name, content):
        self._run('UPDATE configs SET name=?,content=? WHERE id=?', (name, content, ident), write=True)

    def delete_config(self, ident):
        self._run('DELETE FROM configs WHERE id=?', (ident,), write=True)

    def community(self):
        return [dict(id=r[0], name=r[1], content=r[2], **json.loads(r[3]))
                for r in self._run('SELECT id,name,content,metadata FROM community ORDER BY rowid DESC')]

    def add_community(self, name, content, meta):
        ident = uuid.uuid4().hex
        self._run('INSERT INTO community VALUES (?,?,?,?)', (ident, name, content, json.dumps(meta)), write=True)
        return ident

    def delete_community(self, ident):
        self._run('DELETE FROM community WHERE id=?', (ident,), write=True)
