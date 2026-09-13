# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置：把 UESTC 校园网自动登录打成一个单文件 exe
（内置 Python 解释器和 requests，别人下载后双击就能用，不用装 Python）。

本地构建：

    pip install requests "pyinstaller>=6.11"
    pyinstaller uestc-autologin.spec

产物：dist/UESTC-AutoLogin.exe

GitHub Actions（.github/workflows/release.yml）打包时用的也是这个 spec，
保证本地和 Release 里的东西一致。
"""
import os
import sys

ROOT = SPECPATH  # noqa: F821  PyInstaller 注入的 spec 所在目录
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import __version__  # noqa: E402

# conda（包括 conda 里建的 venv）把 libssl-3-x64.dll / libffi 之类的 DLL 放在
# <prefix>\Library\bin 下，而 PyInstaller 找依赖只认 PATH：不把目录加进去，
# 打出来的 exe 会因为缺 libssl-3-x64.dll / ffi.dll 起不来（requests 一 import
# 就挂）。python.org 的 Python 不需要这一步，加了也无害。
for _base in {sys.base_prefix, sys.prefix}:
    _conda_bin = os.path.join(_base, 'Library', 'bin')
    if os.path.isdir(_conda_bin) and _conda_bin not in os.environ.get('PATH', '').split(os.pathsep):
        os.environ['PATH'] = _conda_bin + os.pathsep + os.environ.get('PATH', '')

ICON = os.path.join(ROOT, 'assets', 'icon.ico')

# Windows 版本资源（exe 属性里的产品名称 / 文件版本）。
version_file = os.path.join(workpath, 'version_info.txt')  # noqa: F821
try:
    from tools.make_version_info import write_version_file

    write_version_file(version_file, __version__)
except Exception as exc:  # 生成不出来也别挡住打包
    print('[spec] 版本资源生成失败，跳过：{}'.format(exc))
    version_file = None

a = Analysis(
    ['app.py'],
    pathex=[ROOT],
    binaries=[],
    # config.example.toml 是首次运行时生成 config.toml 用的模板，必须打进去
    datas=[('config.example.toml', '.')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # 控制台程序用不上 tkinter，排掉能小一圈
    excludes=['tkinter', '_tkinter'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='UESTC-AutoLogin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,            # 控制台菜单，双击就是一个黑窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
    version=version_file,
)