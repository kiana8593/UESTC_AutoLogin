#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
UESTC 校园网自动登录 —— 统一入口（打包成单文件 exe 后双击运行的就是它）。

不带参数进入控制台菜单；带参数执行对应动作，开机计划任务就是用
`--daemon` 来调它的。

几点约定：
* 配置和日志都放在程序所在目录（见 paths.py），绿色便携；
* 装 / 卸开机计划任务需要管理员权限，没有权限时会自我提权重启；
* 顶层不 import config / always_online —— 配置文件还没生成时要能优雅地走首次运行流程。
"""
import argparse
import ctypes
import os
import subprocess
import sys
import time
from pathlib import Path

from paths import APP_DIR

__version__ = '1.0.0'

CONFIG_FILE = APP_DIR / 'config.toml'
CONSOLE_LOG = 'always_online.console.log'
TASK_NAME = 'UESTC AutoLogin'
STARTUP_FILE_NAME = 'UESTC AutoLogin.cmd'
IS_WINDOWS = os.name == 'nt'
IS_FROZEN = bool(getattr(sys, 'frozen', False))

# ------------------------------------------------------------------ 小工具

def fix_console_encoding():
    """
    让 print 中文永远不会因为编码问题把程序干掉。

    中文 Windows 控制台是 GBK（能编中文）；但把输出重定向给管道 / 文件时，
    Python 用的是系统 ANSI 码页 —— 英文系统上是 cp1252，编不出中文，一句
    print('中文') 就抛 UnicodeEncodeError 直接退出（CI 上就踩了这个坑：
    --help 里全是中文，一跑就崩）。所以：

    * 输出到控制台：保留原编码，只把 errors 改成 replace；
    * 输出重定向到文件 / 管道：直接换成 utf-8。
    """
    for name in ('stdout', 'stderr'):
        stream = getattr(sys, name, None)
        if stream is None or not hasattr(stream, 'reconfigure'):
            continue
        try:
            if stream.isatty():
                stream.reconfigure(errors='replace')
            else:
                stream.reconfigure(encoding='utf-8', errors='replace')
        except Exception:
            pass


fix_console_encoding()


def decode(raw):
    """计划任务等系统命令的输出是本地编码（中文系统是 GBK），统一解码。"""
    for enc in ('mbcs', 'utf-8', 'gbk'):
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode('utf-8', 'replace')


def run_cmd(cmd):
    """跑一条系统命令，返回 (returncode, 合并后的输出文本)。"""
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as exc:
        return 1, str(exc)
    return proc.returncode, decode(proc.stdout or b'')


REPORT_FILE = APP_DIR / 'logs' / 'task-report.txt'


def write_report(text):
    """把管理员那次操作的结果写到 logs/ 下：原窗口要回显，事后也能查。"""
    try:
        REPORT_FILE.parent.mkdir(parents=True, exist_ok=True)
        REPORT_FILE.write_text(text, encoding='utf-8')
    except OSError:
        pass


def read_report():
    try:
        return REPORT_FILE.read_text(encoding='utf-8')
    except OSError:
        return ''


def clear_report():
    try:
        REPORT_FILE.unlink()
    except OSError:
        pass


def is_admin():
    if not IS_WINDOWS:
        return os.geteuid() == 0
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def self_command_args(flag):
    """自我提权时要传的参数：打包后直接是 exe，源码运行要带上脚本路径。"""
    if IS_FROZEN:
        return [flag]
    return [str(Path(__file__).resolve()), flag]


class SHELLEXECUTEINFO(ctypes.Structure):
    """ShellExecuteExW 的参数结构（只用得到 runas + 拿子进程句柄）。"""

    _fields_ = [
        ('cbSize', ctypes.c_ulong),
        ('fMask', ctypes.c_ulong),
        ('hwnd', ctypes.c_void_p),
        ('lpVerb', ctypes.c_wchar_p),
        ('lpFile', ctypes.c_wchar_p),
        ('lpParameters', ctypes.c_wchar_p),
        ('lpDirectory', ctypes.c_wchar_p),
        ('nShow', ctypes.c_int),
        ('hInstApp', ctypes.c_void_p),
        ('lpIDList', ctypes.c_void_p),
        ('lpClass', ctypes.c_wchar_p),
        ('hkeyClass', ctypes.c_void_p),
        ('dwHotKey', ctypes.c_ulong),
        ('hIcon', ctypes.c_void_p),      # 与 hMonitor 共用一块内存
        ('hProcess', ctypes.c_void_p),
    ]


SEE_MASK_NOCLOSEPROCESS = 0x00000040
WAIT_TIMEOUT = 0x00000102
WAIT_MS = 5 * 60 * 1000          # 最多等管理员那边 5 分钟（UAC 想点多久都行）


def relaunch_elevated(flag):
    """
    用 UAC 提权重启自己，跑完把结果带回来。

    提权后的进程有自己的控制台窗口，输出看不见；而且它一结束窗口就关了。
    所以这里用 ShellExecuteExW 拿子进程句柄等它跑完，再把它写下的报告读回来，
    原窗口（用户双击的那个）里就能看到装没装上。
    """
    if not IS_WINDOWS:
        return False

    clear_report()
    params = subprocess.list2cmdline(self_command_args(flag))
    sei = SHELLEXECUTEINFO()
    sei.cbSize = ctypes.sizeof(SHELLEXECUTEINFO)
    sei.fMask = SEE_MASK_NOCLOSEPROCESS
    sei.lpVerb = 'runas'
    sei.lpFile = sys.executable
    sei.lpParameters = params
    sei.lpDirectory = str(APP_DIR)
    sei.nShow = 1

    print('需要管理员权限：请在接下来弹出的 UAC 窗口里点「是」...')
    try:
        ok = ctypes.windll.shell32.ShellExecuteExW(ctypes.byref(sei))
    except Exception as exc:
        print(f'提权失败：{exc}')
        return False
    if not ok or not sei.hProcess:
        print('提权失败（多半是点了「否」）。请右键程序 →「以管理员身份运行」再试。')
        return False

    ctypes.windll.kernel32.WaitForSingleObject(sei.hProcess, WAIT_MS)
    code = ctypes.c_ulong(0)
    ctypes.windll.kernel32.GetExitCodeProcess(sei.hProcess, ctypes.byref(code))
    ctypes.windll.kernel32.CloseHandle(sei.hProcess)

    report = read_report()
    if report:
        print('--- 管理员窗口里的结果 ---')
        print(report.strip())
        print('--------------------------')
    return code.value == 0


def pause(message='按回车继续...'):
    try:
        input(message)
    except (EOFError, KeyboardInterrupt):
        print()


def program_target():
    """计划任务 / 启动项里要执行的命令（--daemon 由调用方拼）。"""
    if IS_FROZEN:
        return f'"{sys.executable}"'
    return f'"{sys.executable}" "{Path(__file__).resolve()}"'


# ------------------------------------------------------------------ 配置

def ensure_config_file(open_editor=True):
    """确保 config.toml 存在；这次新建了返回 True 并给出填写指引。"""
    from config import ensure_config

    if not ensure_config():
        return False

    print()
    print('=' * 56)
    print(f' 已生成配置文件：{CONFIG_FILE}')
    print(' 请把「你的学号」「你的密码」改成你自己的，保存后再回来登录。')
    print(' 校园网：@dx-uestc   电信：@dx   移动：@cmcc')
    print('=' * 56)
    if open_editor:
        open_config_in_editor()
    return True


def open_config_in_editor():
    if not CONFIG_FILE.exists():
        ensure_config_file(open_editor=False)
    try:
        if IS_WINDOWS:
            os.startfile(str(CONFIG_FILE))  # noqa: S606
        else:
            subprocess.Popen(['xdg-open', str(CONFIG_FILE)])
    except Exception as exc:
        print(f'打开编辑器失败：{exc}')
        print(f'请手动编辑：{CONFIG_FILE}')
        return 1
    print(f'已用默认编辑器打开：{CONFIG_FILE}')
    return 0


def load_options():
    from config import load_config
    return load_config()


# ------------------------------------------------------------------ 各种动作

def do_login():
    if not CONFIG_FILE.exists():
        ensure_config_file()
        return 1
    from BitSrunLogin.LoginManager import LoginManager

    try:
        options = load_options()
    except Exception as exc:
        print(f'读取配置失败：{exc}')
        return 1

    user = options['user']
    print(f"开始登录 {options['url']} (ac_id={options['ac_id']}, domain={options['domain']}) ...")
    try:
        LoginManager(**options).login(username=user.user_id, password=user.passwd)
    except Exception as exc:
        print(f'登录过程出错：{exc}')
        return 1
    return 0


def do_daemon():
    """常驻：掉线自动重连。给开机计划任务用，所以把输出重定向到日志文件。"""
    if not CONFIG_FILE.exists():
        print(f'找不到配置文件：{CONFIG_FILE}')
        return 1

    logs_dir = APP_DIR / 'logs'
    logs_dir.mkdir(parents=True, exist_ok=True)
    console = open(logs_dir / CONSOLE_LOG, 'a', encoding='utf-8', buffering=1)
    sys.stdout = console
    sys.stderr = console

    try:
        from always_online import always_login
        while True:
            try:
                always_login(**load_options())
            except Exception:
                import traceback
                traceback.print_exc()
                time.sleep(15)
    finally:
        console.flush()


def task_run_command():
    return program_target() + ' --daemon'


def install_task():
    if IS_WINDOWS and not is_admin():
        return 0 if relaunch_elevated('--install-task') else 1

    run_command = task_run_command()
    rc, out = run_cmd([
        'schtasks', '/Create', '/TN', TASK_NAME, '/TR', run_command,
        '/SC', 'ONSTART', '/DELAY', '0000:30', '/RU', 'SYSTEM', '/RL', 'HIGHEST', '/F',
    ])
    lines = [out.strip()]
    if rc == 0:
        lines += [
            '',
            f'已注册开机计划任务：{TASK_NAME}',
            f'  启动命令：{run_command}',
            '  开机 30 秒后以 SYSTEM 身份启动，不需要登录 Windows。',
            f'  日志：{APP_DIR / "logs"}',
        ]
        if IS_FROZEN and any(part in str(APP_DIR).lower() for part in ('\\temp\\', '\\downloads\\')):
            lines.append('  ⚠ 程序现在放在临时目录 / 下载目录，装了自启后请不要再移动它。')
    else:
        lines.append('注册失败：请确认是以管理员身份运行，并且程序放在固定目录。')
    print('\n'.join(lines))
    write_report('\n'.join(lines) + '\n')
    return rc


def remove_task():
    if IS_WINDOWS and not is_admin():
        return 0 if relaunch_elevated('--remove-task') else 1
    rc, out = run_cmd(['schtasks', '/Delete', '/TN', TASK_NAME, '/F'])
    lines = [out.strip()]
    if rc == 0:
        lines.append(f'已删除开机自启：{TASK_NAME}')
    print('\n'.join(lines))
    write_report('\n'.join(lines) + '\n')
    return rc


def task_status(verbose=True):
    rc, out = run_cmd(['schtasks', '/Query', '/TN', TASK_NAME, '/V', '/FO', 'LIST'])
    if verbose:
        if rc == 0:
            print(out.strip())
        elif IS_WINDOWS and not is_admin():
            print('没有管理员权限，读不到 SYSTEM 任务的详情。')
            print('  想看详情：右键程序 →「以管理员身份运行」，再选 5。')
            print(f'  也可以直接看日志时间戳：{APP_DIR / "logs"} ')
            report = read_report()
            if report:
                print()
                print('  最近一次安装 / 卸载的结果（logs/task-report.txt）：')
                for line in report.strip().splitlines():
                    print(f'    {line}')
        else:
            print('没有安装开机自启。')
            print(out.strip())
    return rc, out


def startup_file():
    appdata = os.environ.get('APPDATA')
    if not appdata:
        return None
    return (Path(appdata) / 'Microsoft' / 'Windows' / 'Start Menu'
            / 'Programs' / 'Startup' / STARTUP_FILE_NAME)


def install_startup():
    path = startup_file()
    if path is None:
        print('找不到启动文件夹（环境变量 APPDATA 为空）。')
        return 1
    body = ('@echo off\r\n'
            'rem UESTC AutoLogin - start the reconnect monitor after logon\r\n'
            f'start "" {program_target()} --daemon\r\n')
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding='gbk', errors='replace')
    except OSError as exc:
        print(f'写入失败：{exc}')
        return 1
    print(f'已安装「登录后自启」：{path}')
    print('登录 Windows 后会自动启动守候进程（这次登录不会立刻生效）。')
    return 0


def remove_startup():
    path = startup_file()
    if path is None:
        print('找不到启动文件夹。')
        return 1
    if not path.exists():
        print('没有安装「登录后自启」。')
        return 0
    try:
        path.unlink()
    except OSError as exc:
        print(f'删除失败：{exc}')
        return 1
    print(f'已卸载「登录后自启」：{path}')
    return 0


# ------------------------------------------------------------------ 菜单

def brief_status():
    state = '已填写' if CONFIG_FILE.exists() else '未创建'
    print(f'  配置：{CONFIG_FILE}  [{state}]')
    rc, _ = run_cmd(['schtasks', '/Query', '/TN', TASK_NAME, '/FO', 'LIST'])
    if rc == 0:
        print('  开机自启：已安装（开机就跑，不用登录）')
    elif IS_WINDOWS and not is_admin():
        print('  开机自启：无法确认（SYSTEM 任务要管理员权限才看得到）')
    else:
        print('  开机自启：未安装')
    link = startup_file()
    if link is not None and link.exists():
        print('  登录后自启：已安装')

def startup_menu():
    while True:
        print()
        print('--- 登录后自启（启动文件夹，不需要管理员）---')
        print(' 1) 安装')
        print(' 2) 卸载')
        print(' 0) 返回')
        try:
            choice = input(' 请选择: ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if choice == '1':
            install_startup()
            pause()
        elif choice == '2':
            remove_startup()
            pause()
        elif choice == '0':
            return


def menu():
    if not CONFIG_FILE.exists():
        print('首次运行：没有找到配置文件，正在生成 ...')
        ensure_config_file(open_editor=True)
        pause('填好学号、密码并保存后，按回车回到菜单...')

    while True:
        print()
        print('=' * 58)
        print(f' UESTC 校园网自动登录  v{__version__}')
        brief_status()
        print('=' * 58)
        print(' 1) 登录一次')
        print(' 2) 常驻：掉线自动重连（前台运行，Ctrl+C 退出）')
        print(' 3) 安装开机自启（开机就跑，不用登录，需要管理员）')
        print(' 4) 卸载开机自启')
        print(' 5) 查看开机自启详情')
        print(' 6) 登录后自启（启动文件夹）安装 / 卸载')
        print(' 7) 编辑 config.toml')
        print(' 8) 打开日志目录')
        print(' 0) 退出')
        try:
            choice = input(' 请选择: ').strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0

        try:
            if choice == '1':
                do_login()
                pause()
            elif choice == '2':
                print('开始常驻，按 Ctrl+C 退出 ...')
                do_daemon()
            elif choice == '3':
                install_task()
                pause()
            elif choice == '4':
                remove_task()
                pause()
            elif choice == '5':
                task_status()
                pause()
            elif choice == '6':
                startup_menu()
            elif choice == '7':
                open_config_in_editor()
                pause()
            elif choice == '8':
                logs_dir = APP_DIR / 'logs'
                logs_dir.mkdir(parents=True, exist_ok=True)
                if IS_WINDOWS:
                    os.startfile(str(logs_dir))  # noqa: S606
                print(f'日志目录：{logs_dir}')
                pause()
            elif choice == '0':
                return 0
            else:
                print('没有这个选项。')
        except KeyboardInterrupt:
            print('\n已中断。')


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog='UESTC-AutoLogin',
        description='UESTC 校园网自动登录（不带参数运行会进入菜单）')
    parser.add_argument('--version', action='version', version=f'UESTC-AutoLogin {__version__}')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--login', action='store_true', help='登录一次后就退出')
    group.add_argument('--daemon', action='store_true', help='常驻：掉线自动重连（给开机计划任务用）')
    group.add_argument('--install-task', action='store_true', help='安装开机自启（计划任务，需要管理员）')
    group.add_argument('--remove-task', action='store_true', help='卸载开机自启（计划任务）')
    group.add_argument('--task-status', action='store_true', help='查看开机自启状态')
    group.add_argument('--install-startup', action='store_true', help='安装「登录后自启」')
    group.add_argument('--remove-startup', action='store_true', help='卸载「登录后自启」')
    group.add_argument('--edit-config', action='store_true', help='编辑 config.toml')

    args = parser.parse_args(argv)

    if args.login:
        return do_login()
    if args.daemon:
        return do_daemon()
    if args.install_task:
        return install_task()
    if args.remove_task:
        return remove_task()
    if args.task_status:
        return task_status()[0]
    if args.install_startup:
        return install_startup()
    if args.remove_startup:
        return remove_startup()
    if args.edit_config:
        return open_config_in_editor()
    return menu()


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('\n已退出。')
        sys.exit(0)