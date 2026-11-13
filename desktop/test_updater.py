import copy
import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
from updater import parse_release, repository, version_tuple, download, ASSET, HTTPSRedirect

PAYLOAD=b'fake installer for transport verification only'
REPO='xartezz/settingscs2'
DATA={'tag_name':'v0.6.0','draft':False,'prerelease':False,'assets':[{'name':ASSET,'state':'uploaded','size':len(PAYLOAD),'digest':'sha256:'+hashlib.sha256(PAYLOAD).hexdigest(),'browser_download_url':'https://github.com/'+REPO+'/releases/download/v0.6.0/'+ASSET}]}
class Updates(unittest.TestCase):
    def test_versions(self):
        self.assertGreater(version_tuple('v0.10.0'),version_tuple('0.9.9'))
        self.assertIsNone(parse_release(DATA,REPO,'0.6.0'))
        self.assertIsNone(parse_release(DATA,REPO,'1.0.0'))
        for bad in ['v1.2','1.2.3-beta','1.2.3/evil']:
            with self.assertRaises(ValueError):version_tuple(bad)
    def test_repository(self):
        for bad in ['https://github.com/a/b','a/../b','a/b?q=x','a/b/c']:
            with self.assertRaises(ValueError):repository(bad)
    def test_release_validation(self):
        for key,value in [('browser_download_url','https://evil.example/setup.exe'),('digest',''),('size',-1)]:
            data=copy.deepcopy(DATA);data['assets'][0][key]=value
            with self.assertRaises(ValueError):parse_release(data,REPO,'0.5.0')
        data=copy.deepcopy(DATA);data['prerelease']=True
        self.assertIsNone(parse_release(data,REPO,'0.5.0'))
    def test_download_and_integrity(self):
        release=parse_release(DATA,REPO,'0.5.0')
        with tempfile.TemporaryDirectory() as directory:
            opener=Mock();opener.open.return_value=io.BytesIO(PAYLOAD)
            with patch('updater.urllib.request.build_opener',return_value=opener):
                target=download(release,directory);self.assertEqual(target.read_bytes(),PAYLOAD)
            bad=dict(release,sha256='0'*64);opener.open.return_value=io.BytesIO(PAYLOAD)
            with patch('updater.urllib.request.build_opener',return_value=opener):
                with self.assertRaises(ValueError):download(bad,directory)
            self.assertEqual(len(list(Path(directory).rglob('*.exe'))),1)
    def test_rebrand_prefers_new_asset_and_accepts_legacy(self):
        data=copy.deepcopy(DATA)
        legacy=copy.deepcopy(data['assets'][0])
        legacy['name']='SettingsCS2-Setup.exe'
        legacy['browser_download_url']=legacy['browser_download_url'].replace(ASSET,legacy['name'])
        data['assets'].append(legacy)
        self.assertTrue(parse_release(data,REPO,'0.5.0')['url'].endswith(ASSET))
        data['assets']=[legacy]
        self.assertTrue(parse_release(data,REPO,'0.5.0')['url'].endswith('SettingsCS2-Setup.exe'))
        legacy['browser_download_url']='https://evil.example/SettingsCS2-Setup.exe'
        with self.assertRaises(ValueError):parse_release(data,REPO,'0.5.0')
    def test_block_redirect(self):
        with self.assertRaises(ValueError):HTTPSRedirect().redirect_request(None,None,302,'',{},'http://evil.example/file')
if __name__=='__main__':unittest.main()

