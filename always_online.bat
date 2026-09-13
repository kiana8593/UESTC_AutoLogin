@echo off
rem ============================================================
rem  UESTC campus network keeper: stays resident, reconnects on drop.
rem  Used by the Startup shortcut (see setup_startup.ps1).
rem
rem  Run autoConnectNetwork.bat instead if you just want a one-shot login.
rem  This window IS the keeper process: closing it stops auto reconnect.
rem
rem  NOTE: keep this file ASCII-only. cmd parses .bat with the OEM code
rem  page (936 here), and non-ASCII bytes in here can break parsing.
rem ============================================================
cd /d "%~dp0"

rem Absolute path of your python.exe. conda keeps python.exe in the
rem install root (not in PATH), so the full path is needed here.
if not defined PYTHON set "PYTHON=D:\APPs\anaconda3\python.exe"
if not exist "%PYTHON%" (
    echo.
    echo [ERROR] python.exe not found at: %PYTHON%
    echo Open this file and fix the PYTHON path above.
    echo.
    pause
    exit /b 1
)

title UESTC AutoLogin - always online
"%PYTHON%" -u "%~dp0always_online.py"

echo.
echo [AutoLogin] monitor stopped. Exit code: %ERRORLEVEL%
if not "%ERRORLEVEL%"=="0" pause
