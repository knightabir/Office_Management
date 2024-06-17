@echo off
REM WEB SERVER STOP SCRIPT

REM Set environment variables
set PID_HOME=%USERPROFILE%\xbuild\.proc\tmp\marline
set APPLICATION=main.py

REM Read PID from file
if exist %PID_HOME%\%APPLICATION%.pid (
    set /p PID=<%PID_HOME%\%APPLICATION%.pid

    REM Debugging output
    echo Stopping server with PID: %PID%

    REM Kill the process
    taskkill /PID %PID% /F

    REM Remove the PID file
    del %PID_HOME%\%APPLICATION%.pid

    echo Server stopped.
) else (
    echo PID file not found. Server may not be running.
)
