@echo off
cd disk\Live\live\bilibili-live-recorder-master
call disk\to\to\anaconda3\Scripts\activate.bat Universal

:check_connection
ping -n 1 google.com >nul 2>&1
if errorlevel 1 (
    echo Waiting for network connection...
    timeout /t 5 >nul
    goto check_connection
)

echo The network is connected, execute the script...
python combination.py

