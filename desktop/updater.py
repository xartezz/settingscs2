"""Public GitHub Releases updater. HTTPS, bounded download, SHA-256 verification."""
import hashlib
import json
import re
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ASSET = 'SettingsCS2-Setup.exe'
LIMIT = 200 * 1024 * 1024


def version_tuple(version):
    if not isinstance(version, str) or not re.fullmatch(r'v?(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', version):
        raise ValueError('Versiunea trebuie să fie de forma v0.5.0.')
    return tuple(map(int, version.lstrip('v').split('.')))


def repository(value):
    value = value.strip()
    if not re.fullmatch(r'[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9_.-]{1,100}', value) or value.split('/')[1] in ('.','..'):
        raise ValueError('Introdu repository-ul ca utilizator/settingscs2, fără https://. Folosește numai repository-ul tău de încredere.')
    return value


def request(url):
    return urllib.request.Request(url, headers={'User-Agent':'SettingsCS2-Updater','Accept':'application/vnd.github+json'})


def latest(repo, current):
    repo = repository(repo)
    try:
        with urllib.request.urlopen(request(f'https://api.github.com/repos/{repo}/releases/latest'), timeout=20) as response:
            raw=response.read(2*1024*1024+1)
    except urllib.error.HTTPError as error:
        if error.code==404:raise ValueError('Nu există încă o versiune publică. Verifică repository-ul și prima publicare în Releases.') from error
        if error.code in (403,429):raise ValueError('GitHub limitează momentan cererile. Încearcă mai târziu.') from error
        raise
    if len(raw)>2*1024*1024:raise ValueError('Răspuns GitHub prea mare.')
    return parse_release(json.loads(raw),repo,current)


def parse_release(data,repo,current):
    repo=repository(repo)
    if data.get('draft') or data.get('prerelease'):return None
    tag=data.get('tag_name','')
    if version_tuple(tag)<=version_tuple(current):return None
    candidates=[a for a in data.get('assets',[]) if a.get('name')==ASSET and a.get('state')=='uploaded']
    if len(candidates)!=1:raise ValueError('Release-ul nu conține installerul complet. Verifică Actions.')
    asset=candidates[0];digest=asset.get('digest','')
    if not isinstance(digest,str) or not re.fullmatch(r'sha256:[a-fA-F0-9]{64}',digest):
        raise ValueError('Installerul nu are un SHA-256 verificabil în GitHub. Actualizarea a fost oprită.')
    size=asset.get('size')
    if not isinstance(size,int) or not 0<size<=LIMIT:raise ValueError('Dimensiune installer invalidă.')
    url=asset.get('browser_download_url','')
    expected=f'https://github.com/{repo}/releases/download/{tag}/{ASSET}'
    if url!=expected:raise ValueError('Adresa installerului nu corespunde repository-ului ales.')
    return dict(version=tag.lstrip('v'),url=url,sha256=digest[7:].lower(),size=size,repo=repo)


class HTTPSRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parts=urllib.parse.urlsplit(newurl)
        if parts.scheme!='https' or parts.hostname not in ('github.com','release-assets.githubusercontent.com','objects.githubusercontent.com'):
            raise ValueError('Redirecționare de download nepermisă.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def download(release, directory):
    # Revalidate the install URL even when called independently of latest().
    repo=repository(release['repo']);version_tuple(release['version'])
    parts=urllib.parse.urlsplit(release['url'])
    if parts.scheme!='https' or parts.hostname!='github.com' or not parts.path.startswith('/'+repo+'/releases/download/'):
        raise ValueError('Adresă de download invalidă.')
    destination=Path(directory);destination.mkdir(parents=True,exist_ok=True)
    folder=Path(tempfile.mkdtemp(prefix='update-',dir=destination))
    temporary=folder/'download.part';target=folder/ASSET
    try:
        digest=hashlib.sha256();size=0
        opener=urllib.request.build_opener(HTTPSRedirect())
        with opener.open(request(release['url']),timeout=45) as response, temporary.open('wb') as output:
            while True:
                block=response.read(1024*1024)
                if not block:break
                size+=len(block)
                if size>LIMIT or size>release['size']:raise ValueError('Download prea mare.')
                digest.update(block);output.write(block)
        if size!=release['size'] or digest.hexdigest()!=release['sha256']:
            raise ValueError('Verificarea SHA-256 a eșuat. Nu s-a instalat nimic.')
        temporary.replace(target)
        return target
    except Exception:
        temporary.unlink(missing_ok=True)
        try:folder.rmdir()
        except OSError:pass
        raise
