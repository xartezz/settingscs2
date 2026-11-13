# PerfSettings

A Windows companion and website for game settings, pro presets and a local config library. Dark red and black styling, compact horizontal navigation, glass-inspired surfaces and rounded animated controls.

## v0.7.1

- PerfSettings branding across the desktop, website, installer and shortcuts.
- First-run intro: select CS2, FiveM or both. Change preferences from **Change games**.
- CS2 supports pro profiles, partial presets, config import, backup and Steam launch with `+exec`.
- FiveM is **Coming soon**. Selecting it saves an interest and displays a placeholder; it does not install configs or launch FiveM.
- Horizontal navigation replaces the tall, empty sidebar. The intro hides navigation, workspace controls and the status footer until selection is complete.
- Persistent animated red waves and drifting particles surround the content; reduced-motion mode shows a static background. Animation jobs are cancelled when the canvas is destroyed.
- Button hover, focus and page animations, with **Reduce motion** in Settings.
- Desktop glass styling is an opaque visual treatment; the website uses backdrop blur where supported.

## Build and update

1. Open **Actions → Build Windows installer → Run workflow**.
2. Select `main` and enter a new version such as `v0.7.1`.
3. Wait for the workflow to succeed. Download **PerfSettings-Setup.exe** from Releases.
4. Existing users can use **Settings → Check for updates → Install & restart**.
5. Launch PerfSettings, select your games, then choose the CS2 folder and Steam.exe in Settings.

The release workflow tests the code, builds the Windows application, packages it with Inno Setup and publishes both the new installer and a compatibility download for older updaters. Never reuse an already public release tag.

## Compatibility

The repository remains `xartezz/settingscs2`, and GitHub Pages remains at `https://xartezz.github.io/settingscs2/`. Renaming the repository or changing hosting requires a separate migration of update and website URLs.

Existing SQLite data stays in `%LOCALAPPDATA%\SettingsCS2\library.sqlite3`. The installer AppId, internal executable `SettingsCS2.exe`, installation directory, AppUserModelID, `settingscs2://` import protocol, browser storage keys and generated config filenames are intentionally retained so existing data, shortcuts and updates remain compatible. Visible product names and new installer downloads use PerfSettings. The release includes `SettingsCS2-Setup.exe` as a byte-identical alias for old updaters.

## Website

Enable **Settings → Pages → Source: GitHub Actions**. Changes to `web/` on `main` run **Deploy website to GitHub Pages**. This deployment does not change the older ChatGPT-hosted site.

## Data and limitations

Pro settings are an offline November 12, 2026 snapshot. Downloads contain sensitivity and viewmodel commands, not the player's original config. Crosshair previews are illustrative and do not modify downloaded presets. DPI and video settings require manual setup.

Community profiles and config libraries are local, not public accounts or cloud sync. Browser and desktop storage are separate. Review imported commands and close CS2 before applying. Overwriting a dedicated config creates a `.bak`; this does not revert every setting changed in-game.

## Development and verification

Source edition: Python 3.10+ with Tkinter; run `desktop/START.bat` on Windows. No extra pip packages are required at runtime.

Run tests with `python -m unittest discover -s desktop -v`.

Tests cover config validation and backups, updater integrity and compatibility, game selection persistence and window geometry/taskbar logic. GUI rendering, Windows installer upgrades, actual taskbar behavior and execution in CS2 still need validation on Windows. The installer is not digitally signed.
