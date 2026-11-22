# -*- coding: utf-8 -*-
"""免 root 推送 bundle 到 UnityCache（依靠 shell 的 MANAGE_EXTERNAL_STORAGE 权限）。

与 lw_bundle_push.py 的区别：不调用 su，直接以 shell 身份 cp。
会把原文件备份到 /sdcard/Download/lw-backup/ 以便回滚。

用法:
    python lw_bundle_push_nosu.py <本地目录> [--limit N] [--dry]
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
TMP = '/data/local/tmp'
BACKUP = '/sdcard/Download/lw-backup'


def sh(cmd):
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True,
                       encoding='utf-8', errors='replace')
    return ((r.stdout or '') + (r.stderr or '')).strip()


def md5_local(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    src = sys.argv[1]
    dry = '--dry' in sys.argv
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    files = sorted(f for f in os.listdir(src) if f.endswith('__data'))
    if limit:
        files = files[:limit]
    print(f'待推送 {len(files)} 个包' + ('  [dry-run]' if dry else ''))

    sh(f'am force-stop {PKG}')
    sh(f'mkdir -p {BACKUP}')

    ok = bad = 0
    for fn in files:
        a, b, _ = fn.split('__')
        lp = os.path.join(src, fn)
        d = f'{UC}/{a}/{b}'
        if dry:
            print(f'  [dry] {a[:10]}/{b[:8]} -> {d}')
            continue
        # 备份原始文件
        if not os.path.exists(lp):
            print(f'  {a[:10]}…  本地缺失')
            bad += 1
            continue
        sh(f'cp -a {d}/__data {BACKUP}/{a}__{b}.data 2>/dev/null')
        sh(f'cp -a {d}/__info {BACKUP}/{a}__{b}.info 2>/dev/null')
        # 推送到 /data/local/tmp 再 cp
        rp = f'{TMP}/lw_{a}__{b}.bin'
        pr = subprocess.run([ADB, 'push', lp, rp], capture_output=True,
                            encoding='utf-8', errors='replace')
        if pr.returncode != 0:
            print(f'  {a[:10]}…  push 失败: {(pr.stderr or "").strip()[:70]}')
            bad += 1
            continue
        out = sh(f'mkdir -p {d} && cp {rp} {d}/__data && chmod 660 {d}/__data && rm -f {rp}')
        # 写 __info：epoch = __data 的 mtime
        info = sh(f'E=$(stat -c %Y {d}/__data) && '
                  f'printf -- "-1\\n%s\\n1\\n__data\\n" $E > {d}/__info && '
                  f'touch -d @$E {d}/__info && echo epoch=$E')
        got = sh(f'md5sum {d}/__data 2>/dev/null').split(' ')[0]
        want = md5_local(lp)
        if got == want:
            ok += 1
            print(f'  {a[:10]}…  {os.path.getsize(lp):>9} B  OK  {info}')
        else:
            bad += 1
            print(f'  {a[:10]}…  MISMATCH  {out[:60]}')
    print(f'\n成功 {ok}, 失败 {bad}')
    if ok and not dry:
        print('请重新启动游戏验证')


if __name__ == '__main__':
    main()
