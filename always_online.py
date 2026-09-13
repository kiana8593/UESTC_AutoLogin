#!/usr/bin/env python
# -*- coding:utf-8 -*-
import ctypes
import os
import subprocess
import time
import platform

from logger import logger
from BitSrunLogin.LoginManager import LoginManager
from config import login_options

# 获取计算机名
host_name = platform.node()
try:
    #  disable the QuickEdit and Insert mode for the current console
    kernel32 = ctypes.windll.kernel32
    kernel32.SetConsoleMode(kernel32.GetStdHandle(-10), 128)
except:
    pass

def is_connect_internet(test_ip):
    if platform.system().lower().startswith('windows'):
        cmd = ['ping', str(test_ip), '-n', '1']
        flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
    else:
        cmd = ['ping', str(test_ip), '-c', '1']
        flags = 0
    try:
        # 用 subprocess 而不是 os.system：打包后 os.system 每次都会闪一下黑框
        proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                             creationflags=flags)
    except OSError:
        return False
    return proc.returncode == 0

def always_login(user=None, test_ip=None, delay=2, max_failed=3, **kwargs):
    time_now = lambda: time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    org_delay = delay
    failed = 0
    logger.info(f'[{time_now()}] [{host_name}] NetWork Monitor StartUp.')
    while True:
        if not is_connect_internet(test_ip):
            failed += 1
            delay = max(0., delay / 2)
            if failed >= max_failed:
                logger.info(f'[{time_now()}] [{host_name}] offline.')
                LoginManager(**kwargs).login(username=user.user_id, password=user.passwd)
        else:
            if failed >= max_failed:
                logger.info(f'[{time_now()}] [{host_name}] online now.')
            failed = 0
            delay = org_delay
        time.sleep(delay)


if __name__ == "__main__":

    while True:
        try:
            always_login(**login_options)
        except:
            import traceback

            error = traceback.format_exc()
            logger.error(error)
            time.sleep(15)
