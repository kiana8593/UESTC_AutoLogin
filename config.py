#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
加载个人配置 config.toml。

学号 / 密码写在 config.toml 里(该文件已被 .gitignore 忽略)，
本文件只是加载器，不用改。
首次使用请把 config.example.toml 复制成 config.toml 再填。
"""
import tomllib
from collections import namedtuple
from pathlib import Path

from paths import APP_DIR, resource

User = namedtuple('User', ['user_id', 'passwd'])

CONFIG_FILE = APP_DIR / 'config.toml'
EXAMPLE_NAME = 'config.example.toml'


def ensure_config(path=CONFIG_FILE):
    """
    没有 config.toml 就从内置模板生成一份，返回 True 表示这次新建了文件。

    打包成 exe 后模板没法靠相对路径找，所以走 paths.resource()。
    """
    path = Path(path)
    if path.exists():
        return False

    template = resource(EXAMPLE_NAME)
    if not template.exists():
        raise FileNotFoundError(f"找不到配置模板 {template}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(template.read_bytes())
    return True


def load_config(path=CONFIG_FILE):
    """读取 config.toml，返回可直接传给 LoginManager / always_login 的参数字典。"""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"找不到配置文件 {path}\n"
            f"请先把 config.example.toml 复制成 config.toml，并填上你的学号和密码。"
        )

    with open(path, 'rb') as f:
        cfg = tomllib.load(f)

    account = cfg['account']
    portal = cfg['portal']
    monitor = cfg.get('monitor', {})

    return {
        'user': User(str(account['username']), str(account['password'])),
        'url': portal['url'],
        'ac_id': str(portal['ac_id']),  # 校验和要按字符串拼接，而 toml 里写的是数字
        'domain': account.get('domain', '@dx'),

        # 下面的一般不用改
        'test_ip': monitor.get('test_ip', '223.5.5.5'),
        'delay': monitor.get('delay', 16),
        'max_failed': monitor.get('max_failed', 3),
    }


def __getattr__(name):
    """
    兼容老写法：login_once.py / always_online.py 里都是
    `from config import login_options`。

    这里改成「按需加载」，而不是模块导入时就读文件 —— 打包成 exe 后首次运行
    时 config.toml 还不存在，如果导入 config 就直接抛 FileNotFoundError，
    app.py 就没法先调 ensure_config() 生成模板了。配置文件真的缺失时，
    访问 login_options 依然会抛出带提示的 FileNotFoundError。
    """
    if name == 'login_options':
        return load_config()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
