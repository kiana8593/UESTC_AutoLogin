#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
生成 PyInstaller 用的 Windows 版本资源文件。

exe 右键「属性 -> 详细信息」里看到的那些字段（产品名称、文件版本……）就是这个
文件决定的；没有它 exe 的版本信息是空的。

用法（本地构建和 CI 都用同一个脚本）：

    python tools/make_version_info.py [输出路径] [版本号]

默认输出 ``build/version_info.txt``，版本号默认取 ``app.__version__``。
uestc-autologin.spec 打包前会自动调这里的 write_version_file()。

注：字符串里的公司名 / 产品名保持 ASCII，避免不同区域设置的构建机上出现
版本资源乱码。
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import __version__ as APP_VERSION  # noqa: E402

PRODUCT_NAME = 'UESTC-AutoLogin'
COMPANY_NAME = 'kiana8593'
DESCRIPTION = 'UESTC campus network auto login'
COPYRIGHT = 'MIT License'
DEFAULT_TARGET = ROOT / 'build' / 'version_info.txt'


def version_tuple(version):
    """'1.2.3' -> (1, 2, 3, 0)，Windows 版本资源要的是 4 个整数。"""
    parts = []
    for chunk in str(version).split('.'):
        digits = ''.join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def build_version_info(version):
    """构造 VSVersionInfo 对象（需要装好 PyInstaller）。"""
    from PyInstaller.utils.win32.versioninfo import (
        FixedFileInfo,
        StringFileInfo,
        StringStruct,
        StringTable,
        VarFileInfo,
        VarStruct,
        VSVersionInfo,
    )

    fixed = version_tuple(version)
    text = '.'.join(str(n) for n in fixed)

    return VSVersionInfo(
        ffi=FixedFileInfo(
            filevers=fixed,
            prodvers=fixed,
            mask=0x3F,
            flags=0x0,
            OS=0x40004,
            fileType=0x1,
            subtype=0x0,
            date=(0, 0),
        ),
        kids=[
            StringFileInfo([
                StringTable('040904B0', [
                    StringStruct('CompanyName', COMPANY_NAME),
                    StringStruct('FileDescription', DESCRIPTION),
                    StringStruct('FileVersion', text),
                    StringStruct('InternalName', PRODUCT_NAME),
                    StringStruct('LegalCopyright', COPYRIGHT),
                    StringStruct('OriginalFilename', PRODUCT_NAME + '.exe'),
                    StringStruct('ProductName', PRODUCT_NAME),
                    StringStruct('ProductVersion', text),
                ]),
            ]),
            VarFileInfo([VarStruct('Translation', [1033, 1200])]),
        ],
    )


def write_version_file(target=DEFAULT_TARGET, version=APP_VERSION):
    """把版本资源写成 PyInstaller 能读的文本文件，返回文件路径字符串。"""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    # 用 str() 而不是 repr()：repr() 生成的文本带 `versioninfo.` 前缀，
    # 而 PyInstaller 读这个文件时是在 versioninfo 模块里 eval 的，
    # 那里的全局名字是 VSVersionInfo / StringTable ...（没有 versioninfo 这个名字）。
    # 用 str() 拿到的就是 PyInstaller 官方那套「# UTF-8 + VSVersionInfo(...)」写法。
    target.write_text(str(build_version_info(version)), encoding='utf-8')
    return str(target)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    target = argv[0] if len(argv) > 0 else DEFAULT_TARGET
    version = argv[1] if len(argv) > 1 else APP_VERSION
    path = write_version_file(target, version)
    print(f'已生成版本资源：{path} (version={version})')
    return 0


if __name__ == '__main__':
    sys.exit(main())