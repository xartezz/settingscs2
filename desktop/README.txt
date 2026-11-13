SETTINGSCS2 DESKTOP v0.6.0

INSTALL
Download SettingsCS2-Setup.exe from the repository's latest GitHub Release.
The installer includes Python; no separate Python installation is required.
For the source edition only, install Python 3.10+ with Tcl/Tk, then run START.bat.

FIRST LAUNCH
1. Open Settings and choose the Counter-Strike Global Offensive folder
   containing game/bin/win64/cs2.exe, then select Steam.exe.
2. Click Verify & save.
3. Choose a pro preset or import a .cfg file. Review its contents.
4. Close CS2, then use Apply config or Apply & launch CS2.
5. To update, open Settings > Check for updates > Install & restart.

INTERFACE
English interface, animated buttons, section icons and detailed inline profiles.
Profiles include Mouse, Crosshair, Viewmodel, Video, Peripherals and Config.
Crosshair zoom and background controls affect the illustration only.
Use Back, Alt+Left or Escape to return. Save editor changes before leaving.
Reduce motion in Settings disables button and page animations.
Custom title bar supports dragging, minimize, maximize, restore and resizing.
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
