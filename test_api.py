import json
import tempfile
import unittest
from pathlib import Path

import detect
from api import Api
from catalog import PLAYERS
from store import Store


def make_game(root):
    cfg = Path(root) / 'game' / 'csgo' / 'cfg'
    cfg.mkdir(parents=True)
    exe = Path(root) / 'game' / 'bin' / 'win64' / 'cs2.exe'
    exe.parent.mkdir(parents=True)
    exe.write_text('x')
    return cfg


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(Path(self.tmp.name) / 'data')
        self.addCleanup(self.store.close)  # runs before tmp cleanup; Windows cannot delete an open database
        self.calls, self.dialogs, self.opened = [], [], []
        self.api = Api(self.store, dialog=lambda kind, **kw: self.dialogs.pop(0),
                       popen=lambda args, **kw: self.calls.append(args), opener=self.opened.append)

    def ok(self, result):
        self.assertTrue(result['ok'], result)
        return result['data']

    def fail(self, result):
        self.assertFalse(result['ok'])
        return result['error']

    def test_games_flow(self):
        self.assertFalse(self.ok(self.api.state())['intro_complete'])
        self.fail(self.api.set_games([]))
        self.assertEqual(self.ok(self.api.set_games(['fivem', 'cs2'])), ['cs2', 'fivem'])
        state = self.ok(self.api.state())
        self.assertTrue(state['intro_complete'])
        self.assertEqual(state['games'], ['cs2', 'fivem'])

    def test_players_and_library(self):
        players = self.ok(self.api.players())
        self.assertEqual(len(players), len(PLAYERS))
        self.assertIn('sensitivity', players[0]['preset'])
        first = self.ok(self.api.save_player(PLAYERS[0]['id']))
        self.assertEqual(first, self.ok(self.api.save_player(PLAYERS[0]['id'])))
        items = self.ok(self.api.library())['items']
        self.assertEqual([i['id'] for i in items], [first])
        self.fail(self.api.save_player('nobody'))

    def test_signature_changes_when_library_changes(self):
        before = self.ok(self.api.library_sig())
        self.ok(self.api.save_player(PLAYERS[0]['id']))
        self.assertNotEqual(before, self.ok(self.api.library_sig()))

    def test_edit_validation_and_delete(self):
        ident = self.store.add_config('a', 'sensitivity 1')
        self.fail(self.api.save_config(ident, '', 'x'))
        self.fail(self.api.save_config(ident, 'ok', '  '))
        self.fail(self.api.save_config('missing', 'ok', 'x'))
        self.ok(self.api.save_config(ident, 'new', 'sensitivity 2'))
        self.assertEqual(self.ok(self.api.get_config(ident))['name'], 'new')
        self.ok(self.api.delete_config(ident))
        self.fail(self.api.get_config(ident))

    def test_import_and_export(self):
        src = Path(self.tmp.name) / 'mine.cfg'
        src.write_text('sensitivity 1.5', encoding='utf-8')
        self.dialogs.append(str(src))
        self.assertEqual(self.ok(self.api.import_file())['name'], 'mine')
        self.dialogs.append(None)
        self.assertIsNone(self.ok(self.api.import_file()))
        bad = Path(self.tmp.name) / 'mine.txt'
        bad.write_text('x')
        self.dialogs.append(str(bad))
        self.fail(self.api.import_file())
        ident = self.store.configs()[0][0]
        out = Path(self.tmp.name) / 'out.cfg'
        self.dialogs.append(str(out))
        self.ok(self.api.export_config(ident))
        self.assertEqual(out.read_text(encoding='utf-8'), 'sensitivity 1.5')

    def test_apply_and_launch(self):
        ident = self.store.add_config('cfg', 'sensitivity 1')
        self.assertIn('Settings', self.fail(self.api.apply_config(ident)))
        game = Path(self.tmp.name) / 'game'
        cfg = make_game(game)
        self.store.put('game', str(game))
        result = self.ok(self.api.apply_config(ident))
        self.assertEqual(result, dict(target='settingscs2_' + ident + '.cfg', backup=False, launched=False))
        self.assertTrue((cfg / result['target']).is_file())
        self.assertTrue(self.ok(self.api.apply_config(ident))['backup'])
        self.assertIn('Steam', self.fail(self.api.apply_config(ident, True)))
        steam = Path(self.tmp.name) / 'Steam.exe'
        steam.write_text('x')
        self.store.put('steam', str(steam))
        self.assertTrue(self.ok(self.api.apply_config(ident, True))['launched'])
        self.assertEqual(self.calls[-1][-2:], ['+exec', 'settingscs2_' + ident + '.cfg'])
        self.assertEqual(self.calls[-1][1:3], ['-applaunch', '730'])

    def test_save_paths_requires_real_game_folder(self):
        self.fail(self.api.save_paths(self.tmp.name, ''))
        game = Path(self.tmp.name) / 'cs'
        make_game(game)
        self.ok(self.api.save_paths(str(game), ''))
        self.fail(self.api.save_paths(str(game), str(game / 'notsteam.exe')))
        self.assertEqual(self.ok(self.api.state())['game'], str(game))

    def test_community(self):
        data = dict(name='n', author='me', mouse='m', keyboard='k', description='d', content='sensitivity 2')
        self.fail(self.api.community_add(dict(data, author='')))
        self.fail(self.api.community_add(dict(data, description='x' * 241)))
        self.fail(self.api.community_add(dict(data, content='')))
        ident = self.ok(self.api.community_add(data))
        self.assertEqual(self.ok(self.api.state())['nickname'], 'me')
        self.assertEqual(self.ok(self.api.community())[0]['author'], 'me')
        lib = self.ok(self.api.community_to_library(ident))
        self.assertEqual(lib, self.ok(self.api.community_to_library(ident)))
        self.ok(self.api.community_delete(ident))
        self.assertEqual(self.ok(self.api.community()), [])

    def test_website_link(self):
        import base64
        payload = base64.urlsafe_b64encode(json.dumps({'name': 'pro', 'cfg': 'sensitivity 1'}).encode()).decode().rstrip('=')
        self.assertEqual(self.ok(self.api.handle_link('settingscs2://import/' + payload))['name'], 'pro')
        self.fail(self.api.handle_link('settingscs2://import/!!'))

    def test_open_url_allowlist(self):
        self.ok(self.api.open_url('https://prosettings.net/players/donk/'))
        self.fail(self.api.open_url('http://prosettings.net/'))
        self.fail(self.api.open_url('https://evil.example/'))
        self.fail(self.api.open_url('file:///c:/windows/system32/calc.exe'))
        self.assertEqual(len(self.opened), 1)

    def test_update_requires_check_and_validates_repo(self):
        self.assertIn('Check', self.fail(self.api.install_update()))
        self.fail(self.api.save_update_settings('https://github.com/x/y', True))
        self.assertEqual(self.ok(self.api.save_update_settings('a/b', False)), 'a/b')
        self.assertFalse(self.ok(self.api.state())['update_auto'])


class DetectTests(unittest.TestCase):
    def test_finds_game_in_second_library(self):
        with tempfile.TemporaryDirectory() as tmp:
            steam, lib2 = Path(tmp) / 'Steam', Path(tmp) / 'Games'
            (steam / 'steamapps').mkdir(parents=True)
            (steam / 'steam.exe').write_text('x')
            make_game(lib2 / 'steamapps' / 'common' / detect.GAME_DIR)
            vdf = '"libraryfolders" { "0" { "path" "%s" } "1" { "path" "%s" } }' % (
                str(steam).replace('\\', '\\\\'), str(lib2).replace('\\', '\\\\'))
            (steam / 'steamapps' / 'libraryfolders.vdf').write_text(vdf)
            found = detect.detect(steam)
            self.assertEqual(found['steam'], str(steam / 'steam.exe'))
            self.assertEqual(found['game'], str(lib2 / 'steamapps' / 'common' / detect.GAME_DIR))

    def test_nothing_found(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(detect.detect(tmp), {'steam': '', 'game': ''})


if __name__ == '__main__':
    unittest.main()
