@echo off
rem ============================================================
rem  一键登录校园网 (双击运行)
rem
rem  想让电脑一直在线、掉线自动重连，把下面的 login_once.py
rem  换成 always_online.py 即可。
rem ============================================================
cd /d "%~dp0"

rem 如果双击时报 "python 不是内部或外部命令"，说明 python 不在 PATH 里，
rem 把下面这行的 rem 去掉，改成你自己 python.exe 的绝对路径：
rem set "PYTHON=D:\APP-D\anaconda3\python.exe"
if not defined PYTHON if defined CONDA_PREFIX set "PYTHON=%CONDA_PREFIX%\python.exe"
if not defined PYTHON set "PYTHON=python"

"%PYTHON%" "%~dp0login_once.py"

echo.
echo Exit code: %ERRORLEVEL%
pause
