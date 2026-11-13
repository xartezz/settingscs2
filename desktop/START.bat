@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto try_python
set "SC2_PYTHON=py -3"
goto check_tk

:try_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto missing_python
set "SC2_PYTHON=python"
goto check_tk

:check_tk
%SC2_PYTHON% -c "import tkinter" >nul 2>nul
if errorlevel 1 goto missing_tk
%SC2_PYTHON% app.py
if errorlevel 1 goto app_error
exit /b 0

:missing_python
echo.
echo SETTINGSCS2 - Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo Enable Add Python to PATH and include Tcl/Tk and IDLE.
echo Close this window and run START.bat again.
echo For a standalone app, download SettingsCS2-Setup.exe from GitHub Releases.
pause
exit /b 1

:missing_tk
echo.
echo Python is installed but Tkinter is missing.
echo Modify your Python installation to include Tcl/Tk and IDLE.
echo Then run START.bat again.
pause
exit /b 1

:app_error
echo.
echo The app stopped with an error. Share the message shown above.
pause
exit /b 1
