# UESTC 电子科技大学网络认证脚本

自动登录校园网 / 寝室宽带，掉线自动重连。配置只写一个 `config.toml`，不用碰代码。

------------------------------

## 下载即用（不用装 Python）

不想折腾 Python / conda 的话，直接用 Release 里的 `UESTC-AutoLogin.exe`
（Windows 10/11 x64，内置 Python 解释器和 `requests`，没有安装过程）：

1. 从 [Releases](../../releases) 下载 `UESTC-AutoLogin.exe`，放到一个以后不会再挪动的
   固定目录，例如 `D:\APPs\UESTC-AutoLogin\`（配置和日志都写在 exe 旁边，绿色便携）；
2. 双击运行。第一次会自动在 exe 旁边生成 `config.toml`，并用记事本打开，
   填上学号、密码、运营商（`@dx` / `@cmcc` / `@dx-uestc`），保存；
3. 回到菜单选 `1) 登录一次`，看到 `The loggin result is: ok` 就说明配置没问题；
4. 想开机就自动连上：选 `3) 安装开机自启` —— 开机 30 秒后以 `SYSTEM` 身份运行，
   **不用登录 Windows**，装的时候会弹一次管理员授权（不保存你的 Windows 密码）。

首次运行 Windows 可能提示「未知发布者」/ SmartScreen 拦截，点「更多信息」→「仍要运行」
即可，原因是 exe 没有买代码签名证书，不是病毒。面向普通用户的中文说明见
[`使用说明.txt`](使用说明.txt)（会随 Release 一起下载）。

> 只想改代码 / 不想用 exe：下面「快速开始」到「双击运行 / 开机自启」几节讲的是源码方式，
> 两种方式可以共存，配置文件格式完全一样。

------------------------------

## 搞这干啥？

- 学校的电信宽带自动掉线太频繁了，移动的稍好一点但也不行（尊贵的移动还屏蔽了游戏串流软件，真是谢谢你）
- 校园网很稳定，很少掉线。但是如果再出现封在家里一个月没法回学校的情况，那就得想办法让电脑一直在线了，不然没法给老板打工。

支持登录以下类型的网络（我都试过的）：

```text
- 校园网有线接入 + 学号认证（主楼，至今可用）
- 移动、电信寝室宽带有线接入 + 学号认证（硕丰 6、7、8 组团那种插网线直接弹出认证页面的，至今可用）
```

------------------------------

## 快速开始

### 1. 装依赖

只需要 `requests`：

```bash
pip install requests
```

读取配置用的是 Python 标准库 `tomllib`，**需要 Python 3.11 或更高版本**。

### 2. 写自己的配置

仓库里只有一份模板 `config.example.toml`。把它复制成 `config.toml`，填上学号和密码：

```bash
# Windows
copy config.example.toml config.toml

# Linux / macOS
cp config.example.toml config.toml
```

`config.toml` 已经被 `.gitignore` 忽略，**不会被提交到仓库**，可以放心写真实密码。

```toml
[account]
username = "你的学号"        # 学号
password = "你的密码"        # 教务处密码
domain   = "@dx"            # 电信 @dx / 移动 @cmcc / 校园网 @dx-uestc

[portal]
url    = "http://10.253.0.235"  # 寝室公寓；主楼有线是 http://10.253.0.237
ac_id  = 3                      # 寝室公寓 3；主楼有线 1

[monitor]
test_ip    = "223.5.5.5"        # 用这个 IP 判断有没有联网（要选本网络 ping 得通的）
delay      = 16                 # 掉线检测间隔(秒)
max_failed = 3                  # 连续失败几次算断网
```

### 3. 试一下能不能登录

先在浏览器里手动注销、断开网络，然后：

```bash
python login_once.py
```

看到 `The loggin result is: ok` 就说明配置没问题。

### 4. 挂着自动重连

```bash
python always_online.py
```

它会定时 ping `test_ip`，发现断网就自动重新登录，断线重连不用管。

------------------------------

## 配置项说明

| 字段 | 说明 |
| --- | --- |
| `account.username` | 学号 |
| `account.password` | 教务处密码 |
| `account.domain` | 网络提供商：电信 `@dx`、移动 `@cmcc`、校园网 `@dx-uestc` |
| `portal.url` | 认证页地址：寝室公寓 `http://10.253.0.235`，主楼有线校园网 `http://10.253.0.237` |
| `portal.ac_id` | 认证页地址里的 `ac_id` 参数：寝室公寓 `3`，主楼有线 `1` |
| `monitor.test_ip` | 用来判断当前是否联网的 IP，能 ping 通就算在线。默认 `223.5.5.5`，详见下方说明 |
| `monitor.delay` | 掉线检测间隔（秒） |
| `monitor.max_failed` | 连续 ping 失败多少次才认为断网 |

`url` 和 `ac_id` 怎么确认？把 `url` 粘进浏览器，认证页地址栏里长得像
`http://10.253.0.235/srun_portal_pc?ac_id=3&theme=pro`，那个 `ac_id` 就是。

`config.py` 只是加载器，把 `config.toml` 读成程序用的字典，**不需要改它**。

------------------------------

## 双击运行 / 开机自启

两个 bat，各管一件事：

- `autoConnectNetwork.bat`：登录一次就退出，用来验证配置能不能登录成功。
- `always_online.bat`：常驻，掉线自动重连。**关掉窗口 = 停止重连**。

想手动挂机就双击 `always_online.bat`。

### 开机自启（两种方式，二选一）

| 方式 | 什么时候启动 | 需要什么 |
| --- | --- | --- |
| `setup_boot_task.ps1` | **开机就跑，不用登录** | 注册时点一次 UAC 管理员授权，不保存任何密码 |
| `setup_startup.ps1` | 登录 Windows 之后 | 无 |

**方式一：开机就跑，不用登录（推荐）**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1
```

它会注册一个叫 `UESTC AutoLogin` 的计划任务：以 `SYSTEM` 身份在开机 30 秒后运行
`always_online.bat`，掉线自动重连。校园网认证是按机器 IP 做的，不依赖桌面会话，
所以**不用保持登录**，也**不用把 Windows 密码存进任务计划程序**。校园网账号密码仍然
只写在 `config.toml` 里（已被 gitignore，不会进仓库）。

这种模式下没有可见的控制台窗口，而 `LoginManager` 的登录结果是 `print` 出来的（不写日志文件），
所以脚本会把它的输出重定向到 `logs/always_online.console.log`，想看登录结果就翻这个文件。

看状态 / 删除：

```powershell
# 看状态（最近一次运行时间、结果码、下次运行时间）
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1 -Status

# 删除这个计划任务
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_boot_task.ps1 -Remove
```

> 任务是以 SYSTEM 身份跑的，普通权限的终端读不到它的状态（`Get-ScheduledTask`
> 会报「拒绝访问」，不是「没注册」）。要看状态请用管理员身份的 PowerShell。
> 想快速判断它有没有在跑，可以看有没有 `python.exe` 以 SYSTEM 身份运行，
> 或者看 `logs/` 里最新日志的时间戳。

**方式二：登录后自启**

跑一次 `setup_startup.ps1`，它会在启动文件夹里建一个快捷方式，指向
`always_online.bat`，以后每次登录 Windows 都会自动把守候进程拉起来（最小化启动）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_startup.ps1
```

不想要了就加 `-Remove`（只删快捷方式，不动任何别的东西）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\setup_startup.ps1 -Remove
```

动手改也可以：Win+R 输入 `shell:startup` 打开启动文件夹，把 `always_online.bat`
的快捷方式丢进去，然后把快捷方式的「起始位置」设成仓库目录即可。

> **二选一**：两个都装的话，每次登录会多起一个守候进程（`setup_boot_task.ps1`
> 检测到启动文件夹里的快捷方式时会提醒你，任务本身也限制了重复实例）。

### python 路径

如果你换了 conda 环境或 python 安装位置（双击后提示 `python 不是内部或外部命令`，
或者窗口一闪而过），打开对应的 bat，把 `set "PYTHON=..."` 改成你的真实路径即可：

```bat
set "PYTHON=D:\APPs\anaconda3\python.exe"
```

> **bat 别写中文**：cmd 用系统码页（这里 936/GBK）解析 bat 文件，中文注释的字节
> 一旦被错误解码，会把 `rem` 注释行当成命令执行、顺带把后面的 `set "PYTHON=..."`
> 一起弄坏。新加的 `always_online.bat` 就是纯 ASCII，改的时候也请保持。

> **conda 用户注意**：conda 只把 `安装目录\Scripts` 加进了 PATH，而 `python.exe`
> 在安装目录**根目录**下，所以双击 bat 时 `python` 常常会落到
> `C:\Users\<你>\AppData\Local\Microsoft\WindowsApps\python.exe` —— 那是微软商店的
> 占位程序，执行会直接返回 9009。这种情况就必须把绝对路径显式写进 bat，
> 或者在「计划任务」里用 conda 的 python 全路径来跑。

------------------------------

## 目录结构

```text
AutoLoginUESTC/
├── UESTC-AutoLogin.exe   # Release 里下载的免 Python 单文件程序（由 app.py 打包）
├── 使用说明.txt           # 面向普通用户的中文说明（随 Release 发布）
├── app.py                # 统一入口：控制台菜单 + 命令行开关，exe 打包的就是它
├── paths.py              # 程序目录 / 打包后资源目录的解析（源码和 exe 都能用）
├── config.example.toml   # 配置模板（提交到仓库）
├── config.toml           # 你的个人配置（已 gitignore，不提交）
├── config.py             # 读取 config.toml 的加载器
├── login_once.py         # 登录一次，用来验证配置
├── always_online.py      # 常驻，掉线自动重连
├── autoConnectNetwork.bat # 双击：登录一次（源码方式）
├── always_online.bat     # 双击 / 开机自启：常驻重连（纯 ASCII）
├── setup_boot_task.ps1   # 开机就跑、不用登录（SYSTEM 计划任务，源码方式）
├── setup_startup.ps1     # 登录后自启（启动文件夹快捷方式，源码方式）
├── uestc-autologin.spec  # PyInstaller 打包配置
├── tools/make_icon.py    # 生成 assets/icon.ico
├── tools/make_version_info.py # 生成 exe 的 Windows 版本资源
├── assets/               # 图标（icon.png / icon.ico）
├── .github/workflows/release.yml # 打 tag 自动构建并发 Release
├── logger.py             # 日志，写在 logs/ 下
└── BitSrunLogin/         # 深澜(srun)认证协议实现
```

------------------------------

## 打包与发版

### 本地打包（生成单文件 exe）

不想动 conda base 的话，先起一个虚拟环境（Python 3.13 需要 `pyinstaller>=6.11`）：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install requests "pyinstaller>=6.11"
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean uestc-autologin.spec
```

产物是 `dist\UESTC-AutoLogin.exe`：单文件，内置 Python 解释器和 `requests`，
别人下载后双击就能用。`uestc-autologin.spec` 会把 `config.example.toml` 作为内置模板
打进去（exe 首次运行靠它生成 `config.toml`），图标用 `assets/icon.ico`，
并排除 `tkinter` 减小体积；`tools/make_version_info.py` 负责生成 exe 右键属性里的
版本信息。

### 云端自动发版（GitHub Actions）

`.github/workflows/release.yml` 在云端 Windows 上构建，两种触发方式：

| 触发 | 结果 |
| --- | --- |
| 手动 `Run workflow` | 只在 Artifacts 里产出 exe / 说明文件，用来试跑，**不发 Release** |
| 推送 `v*` tag | 先校验 tag 与 `app.py` 里的 `__version__` 一致，再打包并创建 Release，附件为 `UESTC-AutoLogin.exe` 和 `使用说明.txt` |

```bash
# 1. 先把 app.py 里的 __version__ 改成要发的版本号（比如 1.0.1）
# 2. 打 tag 并推送
git tag v1.0.1
git push personal v1.0.1
```

发版前提：仓库的 Actions 是开着的（默认开着）。PyInstaller 不能交叉编译，
所以只在 `windows-latest` 上构建，产物是 Windows 10/11 x64。
exe 不做代码签名（证书要钱），所以别人第一次运行会看到 SmartScreen
「未知发布者」提示，`使用说明.txt` 里说明了怎么继续运行。

------------------------------

## 常见问题

**`FileNotFoundError: 找不到配置文件 .../config.toml`**
忘了复制模板。执行 `copy config.example.toml config.toml` 再填上账号。

**`python 不是内部或外部命令`，或双击 bat 一闪而过**
python 不在 PATH 里，见上面「双击运行」一节。bat 末尾的 `pause` 会停住窗口，
所以别急着关，报错信息就在上面。

**`Failed to resolve IP` / `Cannot find local ip in login page html`**
认证页地址填错了（`url` / `ac_id` 不对），或者学校把深澜认证页又改版了。
先用浏览器打开认证页确认地址栏。

**登录成功但立刻又掉线**
`domain` 填错了。电信 `@dx`、移动 `@cmcc`、校园网 `@dx-uestc`，换一个试试。

**日志里一直刷 `offline.`，但其实能正常上网**
`monitor.test_ip` 那个 IP 在你所在网络 ping 不通，守候进程就误判成断线，会每隔几秒
重试一次登录（`logs/*.log` 里会一直刷 `offline.`）。有的校园网会拦掉部分公共 DNS：
实测 UESTC 网络里 `114.114.114.114` 不通，而 `223.5.5.5`、`119.29.29.29`、
`114.114.115.115` 都通。换一个能通的 IP，重启守候进程后生效。

**怎么确认到底登没登上**
`LoginManager` 的登录结果是 `print` 出来的，不写日志文件。三个办法：双击
`autoConnectNetwork.bat` 手动登一次（窗口里会显示 `The loggin result is: ok`）；
看开机任务模式下的 `logs/always_online.console.log`；或者直接看 `logs/` 里
是否还在刷 `offline.`，不刷了说明在线。

------------------------------

### 抄的！抄的！抄的！

- 楼主入学的时候深澜软件的网络认证页面已经经过混淆了，还好 GitHub 有大佬之前写好的登录流程相关代码，
  所以就完全照着抄了这个 <https://github.com/coffeehat/BIT-srun-login-script>
- 好多学校都是这套登录逻辑，所以 GitHub 脚本很多，上边这个链接里也有支持 OpenWrt 的 go 版本。
