@echo off
setlocal
if "%~1"=="" (
  echo Drag a mod file, mod archive, or mod folder onto this file.
  echo.
  pause
  exit /b 1
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 "%~dp0game_mod_guard.py" %*
  set SCAN_EXIT=%errorlevel%
  echo.
  pause
  exit /b %SCAN_EXIT%
)

where python >nul 2>nul
if %errorlevel%==0 (
  python "%~dp0game_mod_guard.py" %*
  set SCAN_EXIT=%errorlevel%
  echo.
  pause
  exit /b %SCAN_EXIT%
)

echo Python is not installed or is not on PATH.
echo.
echo Easy fix:
echo   1. Open the Microsoft Store.
echo   2. Search for Python.
echo   3. Install the newest Python 3 version.
echo   4. Try dragging the mod onto scan-mod.bat again.
echo.
echo Computer-friend fix:
echo   Install Python from https://www.python.org/downloads/
echo   and enable "Add python.exe to PATH" during install.
echo.
pause
exit /b 1
