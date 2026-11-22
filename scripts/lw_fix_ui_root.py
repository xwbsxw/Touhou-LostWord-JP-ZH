# -*- coding: utf-8 -*-
"""root 一次性修复脚本：
  1. 校验 su
  2. 推送 ui_out / ui_text_out 干净包（覆盖上轮损坏的版本）
  3. 权限加固：把这些 bundle 目录改成 ext_data_rw 组可写（2770），
     这样以后无需 root 也能用 lw_bundle_push_nosu.py 更新
  4. 逐包 md5 校验

用法: python lw_fix_ui_root.py [--no-hardening]
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
TMP = '/data/local/tmp'
BACKUP = '/sdcard/Download/lw-backup'
OWNER = 'u0_a469:u0_a469'


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


def collect():
    out = {}
    for d in ('ui_out', 'ui_text_out'):
        p = os.path.join(ROOT, 'lw_work', d)
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if fn.endswith('__data'):
                out[fn] = os.path.join(p, fn)
    return out


def main():
    hardening = '--no-hardening' not in sys.argv
    print('=== 1. 校验 root ===')
    who = sh("su -c id")
    if 'uid=0' not in who:
        print(f'  没有 root: {who[:90]}')
        print('  请先运行临时 root 工具，再执行本脚本')
        return 1
    print(f'  {who[:60]}')

    files = collect()
    print(f'\n=== 2. 推送 {len(files)} 个干净包 ===')
    sh(f'am force-stop {PKG}')
    sh(f"su -c 'mkdir -p {TMP} {BACKUP}'")

    ok = bad = 0
    pushed_dirs = []
    for fn, lp in sorted(files.items()):
        a, b, _ = fn.split('__')
        d = f'{UC}/{a}/{b}'
        rp = f'{TMP}/fx_{a}__{b}.bin'
        pr = subprocess.run([ADB, 'push', lp, rp], capture_output=True,
                            encoding='utf-8', errors='replace')
        if pr.returncode != 0:
            print(f'  {a[:10]}… push 失败')
            bad += 1
            continue
        # 备份 + 覆盖
        sh(f"su -c 'cp -a {d}/__data {BACKUP}/{a}__{b}.data 2>/dev/null'")
        sh(f"su -c 'mkdir -p {d} && cp {rp} {d}/__data && "
           f"chown {OWNER} {d}/__data && chmod 660 {d}/__data && rm -f {rp}'")
        # 写 __info
        sh(f"su -c 'E=$(stat -c %Y {d}/__data) && "
           f"printf -- \"-1\\n%s\\n1\\n__data\\n\" $E > {d}/__info && "
           f"touch -d @$E {d}/__info'")
        got = sh(f"su -c 'md5sum {d}/__data 2>/dev/null'").split(' ')[0]
        if got == md5_local(lp):
            ok += 1
            pushed_dirs.append((a, b))
        else:
            bad += 1
            print(f'  {a[:10]}… MISMATCH')
    print(f'  成功 {ok}, 失败 {bad}')

    if hardening and pushed_dirs:
        print(f'\n=== 3. 权限加固（{len(pushed_dirs)} 个目录）===')
        # 目录改成 group=ext_data_rw、mode 2770，shell 以后可直接写
        chunk = 20
        done = 0
        for i in range(0, len(pushed_dirs), chunk):
            part = pushed_dirs[i:i + chunk]
            cmds = []
            for a, b in part:
                d = f'{UC}/{a}/{b}'
                cmds.append(f'chgrp ext_data_rw {d} 2>/dev/null; chmod 2770 {d} 2>/dev/null; '
                            f'chgrp ext_data_rw {d}/__data {d}/__info 2>/dev/null; '
                            f'chmod 660 {d}/__data {d}/__info 2>/dev/null')
            sh("su -c '" + '; '.join(cmds) + "'")
            done += len(part)
        print(f'  已处理 {done} 个目录')

    print('\n完成。重启游戏验证。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
