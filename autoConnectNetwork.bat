@echo off
rem ============================================================
rem  一键登录校园网 (双击运行)
rem
rem  想让电脑一直在线、掉线自动重连，把下面的 login_once.py
rem  换成 always_online.py 即可。
rem ============================================================
cd /d "%~dp0"

rem python 不在 PATH 里时要把绝对路径写全，见 always_online.bat 里的说明
if not defined PYTHON set "PYTHON=D:\APPs\anaconda3\python.exe"
if not exist "%PYTHON%" (
    echo.
    echo [ERROR] python.exe not found at: %PYTHON%
    echo Open this file and fix the PYTHON path above.
    echo.
    pause
    exit /b 1
)

"%PYTHON%" "%~dp0login_once.py"

echo.
echo Exit code: %ERRORLEVEL%
pause
