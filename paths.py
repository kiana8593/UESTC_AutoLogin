#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
运行目录解析 —— 源码运行和 PyInstaller 打包后都能用。

源码运行：程序目录 = 仓库目录，资源也在仓库里。
打包成单文件 exe 后：sys.executable 是 exe 本身，配置 / 日志要放在 exe 旁边
（绿色便携），而 config.example.toml 这类被打包进去的只读资源在 sys._MEIPASS 里。

以前 config.py / logger.py 直接用 Path(__file__).parent，打包后 __file__ 指向
临时解包目录：配置会找不到，日志会写进临时目录然后随进程退出被删掉。
"""
import sys
from pathlib import Path


def _is_frozen() -> bool:
    return bool(getattr(sys, 'frozen', False))


if _is_frozen():
    APP_DIR = Path(sys.executable).resolve().parent          # exe 所在目录：配置和日志写这里
    RESOURCE_DIR = Path(getattr(sys, '_MEIPASS', APP_DIR))   # 解包目录：只读资源在这里
else:
    APP_DIR = Path(__file__).resolve().parent
    RESOURCE_DIR = APP_DIR


def resource(name: str) -> Path:
    """取打包进来的只读资源（例如 config.example.toml）的路径。"""
    return RESOURCE_DIR / name