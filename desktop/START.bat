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
echo SETTINGSCS2 - Python 3.10 sau mai nou nu a fost gasit.
echo.
echo 1. Instaleaza Python pentru Windows de la:
echo    https://www.python.org/downloads/windows/
echo 2. Daca installerul ofera optiunea, bifeaza Add Python to PATH.
echo 3. Include componenta Tcl/Tk si IDLE daca este optionala.
echo 4. Inchide aceasta fereastra si porneste din nou START.bat.
echo.
echo Aplicatia necesita Python; aceasta arhiva nu este un executabil standalone.
pause
exit /b 1

:missing_tk
echo.
echo Python este disponibil, dar lipseste componenta Tkinter.
echo Modifica instalarea Python si adauga Tcl/Tk si IDLE.
echo Apoi porneste din nou START.bat.
pause
exit /b 1

:app_error
echo.
echo Aplicatia s-a oprit cu o eroare. Trimite mesajul afisat mai sus.
pause
exit /b 1
