"""Developer tool: run the real interface in headless Chromium against the real Api (no Windows needed).

    pip install playwright && playwright install chromium
    python desktop/tools/ui_preview.py [output_folder]

It clicks through the main screens, saves a screenshot of each, and fails on any console error.
"""
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from playwright.sync_api import sync_playwright  # noqa: E402

from api import Api  # noqa: E402
from store import Store  # noqa: E402

INIT = """
window.pywebview = {api: new Proxy({}, {get: (_, name) => (...args) => window.__call(name, JSON.stringify(args))})};
window.addEventListener('DOMContentLoaded', () => window.dispatchEvent(new Event('pywebviewready')));
"""


def main(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    tmp = tempfile.TemporaryDirectory()
    game = Path(tmp.name) / 'cs2'
    (game / 'game' / 'csgo' / 'cfg').mkdir(parents=True)
    (game / 'game' / 'bin' / 'win64').mkdir(parents=True)
    (game / 'game' / 'bin' / 'win64' / 'cs2.exe').write_text('x')
    steam = Path(tmp.name) / 'Steam.exe'
    steam.write_text('x')
    sample = Path(tmp.name) / 'mine.cfg'
    sample.write_text('// my own config\nsensitivity "1.2"\nbind "mouse3" "+jump"\n')
    answers = {'open': str(sample), 'folder': str(game), 'save': str(Path(tmp.name) / 'out.cfg')}
    store = Store(Path(tmp.name) / 'data')
    api = Api(store, dialog=lambda kind, **kw: answers.get(kind), popen=lambda *a, **k: None, opener=lambda u: None)
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1280, 'height': 840})
        page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.expose_function('__call', lambda name, args: getattr(api, name)(*json.loads(args)))
        page.add_init_script(INIT)
        page.goto((HERE.parent / 'ui' / 'index.html').as_uri())

        def shot(name):
            page.wait_for_timeout(350)
            page.screenshot(path=str(out / (name + '.png')))

        page.wait_for_selector('.gamecard')
        shot('01-intro')
        page.click('[data-g=cs2]')
        page.click('[data-act=finish]')
        page.wait_for_selector('.hero')
        shot('02-pro')
        page.click('#nav [data-tab=settings]')
        page.wait_for_selector('#p-game')
        page.click('[data-act=pickGame]')
        page.fill('#p-steam', str(steam))
        page.click('[data-act=savePaths]')
        page.wait_for_selector('.ok')
        shot('03-settings')
        page.click('#nav [data-tab=pro]')
        page.click('[data-act=player]')
        page.wait_for_selector('#sec-mouse')
        shot('04-player')
        page.click('[data-act=addPlayer]')
        page.wait_for_selector('.item')
        shot('05-library')
        page.click('[data-act=import]')
        page.wait_for_selector('.item >> nth=1')
        page.click('.item >> nth=0')
        page.wait_for_selector('pre.code')
        page.click('[data-act=apply][data-launch]')
        page.click('[data-m="1"]')
        page.wait_for_selector('.toast >> text=Launch requested')
        shot('06-applied')
        page.click('#nav [data-tab=community]')
        page.click('[data-act=newCom]')
        page.fill('#c-name', 'Test setup')
        page.fill('#c-author', 'tester')
        page.click('[data-act=pickCfg]')
        page.click('[data-act=saveCom]')
        page.wait_for_selector('[data-act=toLib]')
        shot('07-community')
        page.set_viewport_size({'width': 1000, 'height': 680})
        page.click('#nav [data-tab=pro]')
        page.wait_for_selector('.pcard')
        shot('08-min-size')
        browser.close()
    store.close()
    tmp.cleanup()
    if errors:
        print('Console errors:\n' + '\n'.join(errors))
        return 1
    print('OK, screenshots in', out)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else HERE / 'shots'))
