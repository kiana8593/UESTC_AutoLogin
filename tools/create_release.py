#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
发布 GitHub Release（CI 里用，也可以本地带 token 手工跑一次）。

两个坑：

1. 中文附件名：不管是 `gh release create` 还是 REST API，GitHub 都不会把
   `使用说明.txt` 原样存下来（实测存成 `default.txt`）。所以 Release 里的附件用
   ASCII 名，中文说明放在附件 label 上；仓库里那份仍然叫 `使用说明.txt`。
2. 直接用 Python 调 REST API 而不是 gh CLI：附件名 / 内容都由这里控制，
   不经过 shell 的参数编码，而且可重跑（覆盖旧附件、清掉多余附件）。

跑之前准备好环境变量：

    GH_TOKEN             有 contents:write 的 token（CI 里用 github.token）
    GITHUB_REPOSITORY    owner/repo
    GITHUB_REF_NAME      tag 名，例如 v1.0.0
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app import __version__  # noqa: E402

API = 'https://api.github.com'
UPLOADS = 'https://uploads.github.com'
TIMEOUT = 300

# (本地文件, Release 附件名（ASCII）, 中文说明（GitHub 上显示为附件 label）)
ASSETS = [
    (ROOT / 'dist' / 'UESTC-AutoLogin.exe', 'UESTC-AutoLogin.exe',
     '免 Python 单文件程序（Windows 10/11 x64）'),
    (ROOT / '使用说明.txt', 'UESTC-AutoLogin-guide.txt',
     '使用说明（中文，双击用记事本打开）'),
]


def request(method, url, token, data=None, content_type='application/json'):
    """返回 (status_code, 解析后的 json 或 {'error': ...})。"""
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Authorization', f'Bearer {token}')
    req.add_header('Accept', 'application/vnd.github+json')
    req.add_header('X-GitHub-Api-Version', '2022-11-28')
    req.add_header('User-Agent', 'UESTC-AutoLogin-release')
    if data is not None:
        req.add_header('Content-Type', content_type)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            raw = resp.read()
            return resp.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as exc:
        return exc.code, {'error': exc.read().decode('utf-8', 'replace')}


def main():
    token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
    repo = os.environ.get('GITHUB_REPOSITORY')
    tag = os.environ.get('GITHUB_REF_NAME')
    missing = [n for n, v in (('GH_TOKEN', token), ('GITHUB_REPOSITORY', repo),
                              ('GITHUB_REF_NAME', tag)) if not v]
    if missing:
        print('缺少环境变量：' + ', '.join(missing))
        return 1

    for path, name, _label in ASSETS:
        if not path.exists():
            print(f'找不到要上传的文件：{path}')
            return 1

    title = f'UESTC 校园网自动登录 {tag}（免 Python 单文件版）'
    body = (ROOT / '使用说明.txt').read_text(encoding='utf-8')
    print(f'目标仓库 {repo}，tag {tag}，版本 {__version__}')

    status, rel = request('GET', f'{API}/repos/{repo}/releases/tags/{tag}', token)
    if status == 200:
        print(f'Release 已存在（id={rel["id"]}），更新标题与说明')
        payload = json.dumps({'name': title, 'body': body}).encode('utf-8')
        status, rel = request('PATCH', f'{API}/repos/{repo}/releases/{rel["id"]}',
                              token, payload)
        if status != 200:
            print(f'更新失败：HTTP {status} {rel.get("error")}')
            return 1
    elif status == 404:
        print('Release 不存在，创建')
        payload = json.dumps({'tag_name': tag, 'name': title, 'body': body}).encode('utf-8')
        status, rel = request('POST', f'{API}/repos/{repo}/releases', token, payload)
        if status not in (200, 201):
            print(f'创建失败：HTTP {status} {rel.get("error")}')
            return 1
    else:
        print(f'查询 Release 失败：HTTP {status} {rel.get("error")}')
        return 1

    wanted = {name for _, name, _label in ASSETS}
    for asset in rel.get('assets', []):
        if asset['name'] in wanted:
            print(f'删除旧附件 {asset["name"]}（准备重传）')
        else:
            print(f'删除多余附件 {asset["name"]}')
        code, out = request('DELETE',
                            f'{API}/repos/{repo}/releases/assets/{asset["id"]}', token)
        if code not in (200, 204):
            print(f'  删除失败：HTTP {code} {out.get("error")}')

    for path, name, label in ASSETS:
        data = path.read_bytes()
        url = (f'{UPLOADS}/repos/{repo}/releases/{rel["id"]}/assets'
               f'?name={urllib.parse.quote(name)}&label={urllib.parse.quote(label)}')
        code, out = request('POST', url, token, data, 'application/octet-stream')
        if code not in (200, 201):
            print(f'上传 {name} 失败：HTTP {code} {out.get("error")}')
            return 1
        got = out.get('name')
        extra = '' if got == name else f'（注意：GitHub 存成了 {got}）'
        print(f'已上传 {name}（{len(data)} 字节）{extra} -> {out.get("browser_download_url")}')

    print(f'完成：{rel.get("html_url")}')
    return 0


if __name__ == '__main__':
    sys.exit(main())