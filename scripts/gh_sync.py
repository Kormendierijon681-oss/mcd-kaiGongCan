#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把本地文件同步到 GitHub 仓库。

为什么不用 git push：本机代理只放行 api.github.com，github.com 的 git 传输被拦
（HTTP2 framing / CONNECT 502），所以改用 GitHub Contents API 逐个文件 PUT。

用法：
    python3 scripts/gh_sync.py                 # 同步所有 git 跟踪的文件
    python3 scripts/gh_sync.py index.html      # 只同步指定文件

依赖：gh 已登录（gh auth status）
"""
import base64
import json
import os
import subprocess
import sys

OWNER = "Kormendierijon681-oss"
REPO = "mcd-kaiGongCan"


def gh(args):
    r = subprocess.run(["gh", "api"] + args, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(f"gh api 失败 {' '.join(args[:3])}\n{r.stderr[:300]}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def tracked_files():
    out = subprocess.check_output(["git", "ls-files"], text=True).split()
    return [f for f in out if os.path.isfile(f)]


def remote_sha(path):
    r = subprocess.run(["gh", "api", f"repos/{OWNER}/{REPO}/contents/{path}"],
                       capture_output=True, text=True)
    return json.loads(r.stdout)["sha"] if r.returncode == 0 else None


def put(path, message=None):
    b64 = base64.b64encode(open(path, "rb").read()).decode()
    args = ["-X", "PUT", f"repos/{OWNER}/{REPO}/contents/{path}",
            "-f", "message=" + (message or f"chore: 同步 {path}"),
            "-f", "content=" + b64]
    sha = remote_sha(path)
    if sha:
        args += ["-f", "sha=" + sha]
    gh(args)
    return "更新" if sha else "新建"


def main():
    files = sys.argv[1:] or tracked_files()
    for f in files:
        if not os.path.isfile(f):
            print(f"  ⚠️ 跳过（不存在）: {f}")
            continue
        n = len(open(f, "rb").read())
        print(f"  ✅ {put(f)} {f} ({n:,}B)")
    print(f"\n仓库：https://github.com/{OWNER}/{REPO}")


if __name__ == "__main__":
    main()
