PerfSettings DESKTOP v0.8.0

INSTALL
Download PerfSettings-Setup.exe from the repository's latest GitHub Release.
The installer includes Python; no separate Python installation is required.
For the source edition only, install Python 3.10+, then run START.bat.
The interface uses the Microsoft Edge WebView2 Runtime (included in Windows 11).

FIRST LAUNCH
1. Open Settings. Steam and CS2 are detected automatically; if not, use Choose
   folder (game/bin/win64/cs2.exe) and Choose Steam.exe.
2. Click Verify & save. Applying a config also tries auto-detection if unset.
3. Choose a pro preset or import a .cfg file. Review its contents.
4. Close CS2, then use Apply config or Apply & launch CS2.
5. To update, open Settings > Check for updates > Install & restart.

INTERFACE
English interface, animated buttons, section icons and detailed inline profiles.
Profiles include Mouse, Crosshair, Viewmodel, Video, Peripherals and Config.
Crosshair zoom and background controls affect the illustration only.
Use Back, Alt+Left or Escape to return. Save editor changes before leaving.
Reduce motion in Settings disables button and page animations.
Native window; the title bar follows the dark theme on Windows 10/11 when supported.
The Windows taskbar registration and stable application identity are retained.

DATA AND LIMITATIONS
Local data persists in %LOCALAPPDATA%\SettingsCS2\library.sqlite3.
Each config has a dedicated settingscs2_<uuid>.cfg file. Replacing that file
creates a .bak backup. autoexec.cfg and persistent Steam launch options are
not changed. This backup does not revert every setting changed in-game.
Steam launches with -applaunch 730 +exec settingscs2_<uuid>.cfg.
DPI, video and drivers require manual setup. Review imported commands.
Pro data is an offline November 12, 2026 snapshot, not live settings.
Presets include sensitivity and viewmodel only; they are not original pro files.
Undocumented equipment is marked as such.
Community and profiles are local. App and browser storage remain separate.
Add to app transfers config contents directly; there is no cloud sync.
Large configs can be downloaded and imported manually.

VALIDATION
Automated checks cover config validation, backups, launch arguments, update
integrity and window behavior. Actual Windows integration and CS2 execution
must be checked on a Windows PC.

FIRST-RUN GAME SELECTION (v0.7)
Choose CS2, FiveM or both on the welcome screen. Preferences are stored locally.
FiveM is coming soon: selecting it does not enable config installation for it.
Change games reopens the selection screen. CS2 configs remain saved when hidden.
Glass-inspired panels use opaque shading for legibility, not native backdrop blur.
Legacy data paths, executable identity and config filenames remain stable to
preserve existing installations, taskbar pins and saved data.

LAYOUT v0.7.1
Navigation is horizontal. The centered game intro hides workspace navigation.
A continuously animated backdrop displays red waves and drifting particles.
Reduce motion freezes the backdrop. Hidden windows skip redraws.

INTERFACE REBUILD v0.8.0
The interface is now HTML/CSS/JS (desktop/ui) shown in a native WebView2 window.
The Python logic (core, updater, library, protocol) is unchanged and is tested
without any GUI: python -m unittest discover -s desktop -v
New: automatic Steam and CS2 detection (registry + libraryfolders.vdf).
New: in-app confirmations instead of system dialogs.
Developer preview without Windows: python desktop/tools/ui_preview.py
