import base64, json, tempfile, unittest
from pathlib import Path
from core import decode_link, install_cfg, launch_args, validate_cfg

class Tests(unittest.TestCase):
    def test_link(self):
        payload=base64.urlsafe_b64encode(json.dumps({'name':'Test', 'cfg':'sensitivity "1.2"'}).encode()).decode().rstrip('=')
        self.assertEqual(decode_link('settingscs2://import/'+payload),('Test','sensitivity "1.2"'))
        for bad in ['https://evil', 'settingscs2://import/../../evil']:
            with self.assertRaises(ValueError):decode_link(bad)
    def test_invalid_config(self):
        for value in ['', 'a\0b', 'a'*262145, None]:
            with self.assertRaises(ValueError):validate_cfg(value)
    def test_install_backup_and_no_other_changes(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); cfg=root/'game/csgo/cfg'; cfg.mkdir(parents=True)
            exe=root/'game/bin/win64/cs2.exe'; exe.parent.mkdir(parents=True); exe.touch()
            original=cfg/'autoexec.cfg'; original.write_text('original')
            target,backup=install_cfg(root,'a'*32,'first'); self.assertIsNone(backup)
            target,backup=install_cfg(root,'a'*32,'second')
            self.assertEqual(target.read_text(),'second'); self.assertEqual(backup.read_text(),'first')
            self.assertEqual(original.read_text(),'original')
            with self.assertRaises(ValueError):install_cfg(root,'../../bad','text')
            steam=root/'Steam.exe'; steam.touch()
            self.assertEqual(launch_args(steam,target.name),[str(steam),'-applaunch','730','+exec',target.name])
    def test_invalid_game(self):
        with tempfile.TemporaryDirectory() as t:
            with self.assertRaises(ValueError):install_cfg(t,'a'*32,'text')
if __name__=='__main__':unittest.main()
