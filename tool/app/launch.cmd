@echo off
cd /d "%~dp0"
call python --version >nul 2>&1
if not errorlevel 1 (
  call python launch.py %*
  exit /b
)
call py -3 --version >nul 2>&1
if not errorlevel 1 (
  call py -3 launch.py %*
  exit /b
)
echo Python 3 is required. Install from https://www.python.org/downloads/
echo Enable Python in PATH or install the Python launcher, then reopen this window.
exit /b 1
