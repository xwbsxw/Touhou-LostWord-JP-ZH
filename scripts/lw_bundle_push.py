# -*- coding: utf-8 -*-
"""按 v1.5 规范把 bundle 推到设备 UnityCache，并正确写 __info。

__info 内容必须是:  -1\n<epoch>\n1\n__data\n
其中 epoch == 该目录下 __data 的 mtime（秒），且 __info 自身 mtime 也要设成同一个 epoch。

用法:
    python lw_bundle_push.py <本地目录> [--dry]
本地目录下文件名形如 <A>__<B>__data。
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
# 注意：/data/local/tmp 本身是 1777 可直接写；不要用 su 在里面建子目录，
# 否则子目录归 root:root 755，adb push（shell 用户）写不进去。
TMP = '/data/local/tmp'
BACKUP = '/data/local/tmp/lw-backup'


def sh(cmd):
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True,
                       encoding='utf-8', errors='replace')
    return (r.stdout or '') + (r.stderr or '')


def md5_local(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def write_info(a, b):
    """按 v1.5 规则生成 __info：epoch 取 __data 的 mtime。"""
    d = f'{UC}/{a}/{b}'
    cmd = (
        f"su -c 'E=$(stat -c %Y {d}/__data) && "
        f"printf -- \"-1\\n%s\\n1\\n__data\\n\" $E > {d}/__info && "
        f"touch -d @$E {d}/__info && echo epoch=$E'"
    )
    return sh(cmd).strip()


def main():
    src = sys.argv[1]
    dry = '--dry' in sys.argv
    files = [f for f in os.listdir(src) if f.endswith('__data')]
    print(f'待推送 {len(files)} 个包' + ('  [dry-run]' if dry else ''))

    sh(f'am force-stop {PKG}')
    sh(f'su -c "mkdir -p {TMP} {BACKUP}"')

    ok = bad = 0
    for fn in sorted(files):
        a, b, _ = fn.split('__')
        lp = os.path.join(src, fn)
        d = f'{UC}/{a}/{b}'
        if dry:
            print(f'  [dry] {a[:10]} -> {d}')
            continue
        # 备份原始 __data / __info
        sh(f"su -c 'cp -a {d}/__data {BACKUP}/{a}.data 2>/dev/null'")
        sh(f"su -c 'cp -a {d}/__info {BACKUP}/{a}.info 2>/dev/null'")
        # 推送（直接放 /data/local/tmp 根下）
        rp = f'{TMP}/lw_{a}.bin'
        pr = subprocess.run([ADB, 'push', lp, rp], capture_output=True,
                            encoding='utf-8', errors='replace')
        if pr.returncode != 0 or not os.path.exists(lp):
            print(f'  {a[:10]}…  push 失败: {(pr.stderr or "").strip()[:80]}')
            bad += 1
            continue
        sh(f"su -c 'mkdir -p {d} && cp {rp} {d}/__data && "
           f"chown u0_a469:u0_a469 {d}/__data && chmod 660 {d}/__data && rm -f {rp}'")
        info = write_info(a, b)
        got = sh(f"su -c 'md5sum {d}/__data 2>/dev/null'").split(' ')[0]
        want = md5_local(lp)
        flag = 'OK' if got == want else 'MISMATCH'
        if got == want:
            ok += 1
        else:
            bad += 1
        print(f'  {a[:10]}…  {os.path.getsize(lp):>9} B  {flag}  {info}')
    print(f'\n成功 {ok}, 失败 {bad}')
    if ok and not dry:
        print('请重新启动游戏验证（am force-stop 已执行）')


if __name__ == '__main__':
    main()
