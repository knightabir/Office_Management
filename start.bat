@echo off
REM WEB SERVER START SCRIPT

REM Set environment variables
set PID_HOME=%USERPROFILE%\xbuild\.proc\tmp\marline
set LOG_PATH=.\log
set LOG_FILE=%LOG_PATH%\run.log
set APPLICATION=main.py
set PYTHON_VERSION=python

REM Create necessary directories
if not exist %PID_HOME% mkdir %PID_HOME%
if not exist %LOG_PATH% mkdir %LOG_PATH%

REM Start the application and log output
start /B %PYTHON_VERSION% %APPLICATION% > %LOG_FILE% 2>&1

REM Remove old PID file if exists
if exist %PID_HOME%\%APPLICATION%.pid del %PID_HOME%\%APPLICATION%.pid

REM Pause briefly to ensure the application starts
timeout /t 5 >nul

REM Write new PID to file
for /f "tokens=2 delims=," %%i in ('tasklist /FI "IMAGENAME eq %PYTHON_VERSION%.exe" /FI "WINDOWTITLE eq %APPLICATION%" /FO CSV /NH') do (
    echo %%i > %PID_HOME%\%APPLICATION%.pid
)

echo Server started.
