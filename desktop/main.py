"""PerfSettings desktop launcher: native window around the HTML interface in ./ui."""
import sys
from pathlib import Path

from api import Api
from core import decode_link
from identity import set_app_identity
from release_config import VERSION
from store import Store

WEBVIEW2_URL = 'https://developer.microsoft.com/microsoft-edge/webview2/'


def resource(*parts):
    base = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
    return base.joinpath(*parts)


def register_protocol():
    import winreg
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\settingscs2') as key:
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, 'URL:PerfSettings')
        winreg.SetValueEx(key, 'URL Protocol', 0, winreg.REG_SZ, '')
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, r'Software\Classes\settingscs2\shell\open\command') as key:
        if getattr(sys, 'frozen', False):
            command = f'"{sys.executable}" "%1"'
        else:
            command = f'"{sys.executable}" "{Path(__file__).resolve()}" "%1"'
        winreg.SetValueEx(key, '', 0, winreg.REG_SZ, command)


def message(text, title='PerfSettings'):
    if sys.platform == 'win32':
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text, title, 0x10)
    else:
        print(title + ': ' + text, file=sys.stderr)


def dark_title_bar(title):
    """Best effort: ask Windows for a dark caption so it matches the interface."""
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        hwnd = ctypes.windll.user32.FindWindowW(None, title)
        if hwnd:
            value = ctypes.c_int(1)
            for attribute in (20, 19):
                ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, attribute, ctypes.byref(value), 4)
    except Exception:
        pass


def main():
    set_app_identity()
    store = Store()
    api = Api(store, register=register_protocol if sys.platform == 'win32' else None)
    if sys.platform == 'win32':
        try:
            register_protocol()
        except OSError as error:
            message('Add to app is unavailable: ' + str(error) + '\nManual import still works.')
    if len(sys.argv) > 1 and sys.argv[1].lower().startswith('settingscs2://'):
        result = api.handle_link(sys.argv[1])
        if result['ok']:
            api._set_notice('Config received from the website. Review it before applying.', 'library')
        else:
            api._set_notice(result['error'])

    try:
        import webview
    except ImportError:
        message('The pywebview package is missing. Run: pip install pywebview\nThe installed PerfSettings app already includes it.')
        return 1

    window = webview.create_window('PerfSettings', str(resource('ui', 'index.html')), js_api=api,
                                   width=1280, height=840, min_size=(1000, 680), background_color='#09090b')

    def dialog(kind, filename='', types=()):
        if kind == 'folder':
            result = window.create_file_dialog(webview.FileDialog.FOLDER)
        elif kind == 'save':
            result = window.create_file_dialog(webview.FileDialog.SAVE, save_filename=filename, file_types=tuple(types))
        else:
            result = window.create_file_dialog(webview.FileDialog.OPEN, file_types=tuple(types))
        if isinstance(result, (list, tuple)):
            result = result[0] if result else None
        return str(result) if result else None

    api._dialog = dialog
    api._set_quit(window.destroy)
    window.events.shown += lambda: dark_title_bar('PerfSettings')
    try:
        webview.start(gui='edgechromium' if sys.platform == 'win32' else None)
    except Exception as error:
        message('The window could not start: ' + str(error) +
                '\nPerfSettings needs the Microsoft Edge WebView2 Runtime:\n' + WEBVIEW2_URL)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
