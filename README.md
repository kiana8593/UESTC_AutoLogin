# UESTC 电子科技大学网络认证脚本

自动登录校园网 / 寝室宽带，掉线自动重连。配置只写一个 `config.toml`，不用碰代码。

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
username = "202912272625"   # 学号
password = "your_password"  # 教务处密码
domain   = "@dx"            # 电信 @dx / 移动 @cmcc / 校园网 @dx-uestc

[portal]
url    = "http://10.253.0.235"  # 寝室公寓；主楼有线是 http://10.253.0.237
ac_id  = 3                      # 寝室公寓 3；主楼有线 1

[monitor]
test_ip    = "114.114.114.114"  # 用这个 IP 判断有没有联网
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
| `monitor.test_ip` | 用来判断当前是否联网的 IP，能 ping 通就算在线 |
| `monitor.delay` | 掉线检测间隔（秒） |
| `monitor.max_failed` | 连续 ping 失败多少次才认为断网 |

`url` 和 `ac_id` 怎么确认？把 `url` 粘进浏览器，认证页地址栏里长得像
`http://10.253.0.235/srun_portal_pc?ac_id=3&theme=pro`，那个 `ac_id` 就是。

`config.py` 只是加载器，把 `config.toml` 读成程序用的字典，**不需要改它**。

------------------------------

## 双击运行 / 开机自启

仓库里的 `autoConnectNetwork.bat` 是个通用启动器，双击就能跑 `login_once.py`。
想让它常驻重连，把里面的 `login_once.py` 改成 `always_online.py`。

如果你的 python 不在 PATH 里（双击后提示 `python 不是内部或外部命令`），
打开这个 bat，把这一行前面的 `rem ` 删掉、改成你自己的 python 路径：

```bat
set "PYTHON=D:\APP-D\anaconda3\python.exe"
```

> **conda 用户注意**：conda 只把 `安装目录\Scripts` 加进了 PATH，而 `python.exe`
> 在安装目录**根目录**下，所以双击 bat 时 `python` 常常会落到
> `C:\Users\<你>\AppData\Local\Microsoft\WindowsApps\python.exe` —— 那是微软商店的
> 占位程序，执行会直接返回 9009。这种情况就必须把绝对路径显式写进 bat，
> 或者在「计划任务」里用 conda 的 python 全路径来跑。

开机自启：把 bat 的快捷方式丢进 `shell:startup`（Win+R 输入即可打开启动文件夹）。

------------------------------

## 目录结构

```text
AutoLoginUESTC/
├── config.example.toml   # 配置模板（提交到仓库）
├── config.toml           # 你的个人配置（已 gitignore，不提交）
├── config.py             # 读取 config.toml 的加载器
├── login_once.py         # 登录一次，用来验证配置
├── always_online.py      # 常驻，掉线自动重连
├── autoConnectNetwork.bat# Windows 双击启动器
├── logger.py             # 日志，写在 logs/ 下
└── BitSrunLogin/         # 深澜(srun)认证协议实现
```

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

------------------------------

### 抄的！抄的！抄的！

- 楼主入学的时候深澜软件的网络认证页面已经经过混淆了，还好 GitHub 有大佬之前写好的登录流程相关代码，
  所以就完全照着抄了这个 <https://github.com/coffeehat/BIT-srun-login-script>
- 好多学校都是这套登录逻辑，所以 GitHub 脚本很多，上边这个链接里也有支持 OpenWrt 的 go 版本。
