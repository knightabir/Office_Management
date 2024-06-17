@echo off
REM Define the log file path
set LOG_FILE=.\log\run.log

REM Check if the log file exists
if exist %LOG_FILE% (
    REM Use PowerShell to tail the log file
    powershell -Command "Get-Content -Path '%LOG_FILE%' -Wait -Tail 10"
) else (
    echo Log file not found: %LOG_FILE%
)
