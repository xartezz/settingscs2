@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 goto try_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto try_python
set "SC2_PYTHON=py -3"
goto check_webview

:try_python
where python >nul 2>nul
if errorlevel 1 goto missing_python
python -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" >nul 2>nul
if errorlevel 1 goto missing_python
set "SC2_PYTHON=python"
goto check_webview

:check_webview
%SC2_PYTHON% -c "import webview" >nul 2>nul
if not errorlevel 1 goto run
echo Installing the interface component (pywebview), one time only...
%SC2_PYTHON% -m pip install -r requirements.txt
if errorlevel 1 goto pip_error

:run
%SC2_PYTHON% main.py
if errorlevel 1 goto app_error
exit /b 0

:missing_python
echo.
echo PerfSettings - Python 3.10 or newer was not found.
echo Install Python from https://www.python.org/downloads/windows/
echo Enable Add Python to PATH, close this window and run START.bat again.
echo For a standalone app, download PerfSettings-Setup.exe from GitHub Releases.
pause
exit /b 1

:pip_error
echo.
echo pywebview could not be installed. Check your internet connection and try again.
pause
exit /b 1

:app_error
echo.
echo The app stopped with an error. Share the message shown above.
echo PerfSettings needs the Microsoft Edge WebView2 Runtime (included in Windows 11).
pause
exit /b 1
