"""Windows taskbar identity; must match the Inno Setup shortcuts."""
import ctypes
import sys
from ctypes import wintypes

APP_USER_MODEL_ID = 'SettingsCS2.Desktop'


def set_app_identity():
    if sys.platform != 'win32':
        return False
    try:
        setter = ctypes.WinDLL('shell32', use_last_error=True).SetCurrentProcessExplicitAppUserModelID
        setter.argtypes = [wintypes.LPCWSTR]
        setter.restype = ctypes.c_long
        return setter(APP_USER_MODEL_ID) == 0
    except (OSError, AttributeError):
        return False
