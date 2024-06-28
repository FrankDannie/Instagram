@echo off
:: Set the timeout period (in seconds)
set TIMEOUT_PERIOD=600

:: Start the build process
start /wait python app.py build

:: Wait for the specified timeout period
timeout /t %TIMEOUT_PERIOD% /nobreak

:: Check if the process is still running and terminate it if necessary
tasklist /FI "IMAGENAME eq python.exe" | find /I "python.exe"
if not errorlevel 1 (
    echo Build process did not complete in time. Terminating...
    taskkill /F /IM python.exe
)
