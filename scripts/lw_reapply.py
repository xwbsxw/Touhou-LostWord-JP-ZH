# -*- coding: utf-8 -*-
"""一键重新应用汉化（主表 + 剧情包）。

用途：游戏触发资源/主表版本更新后，服务器会把 files/cache 里的中文表覆盖回日文，
      这时跑一次本脚本即可恢复。

用法：
    python lw_reapply.py            # 主表 + 剧情包
    python lw_reapply.py tables     # 只推主表
    python lw_reapply.py story      # 只推剧情包
    python lw_reapply.py check      # 只检查当前状态（不改动）

会自动 am force-stop 游戏，推送完成后需要手动重新启动游戏。
"""
import os, sys, json, hashlib, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
CACHE = f'/data/data/{PKG}/files/cache'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
OWNER = 'u0_a469:u0_a469'


def sh(cmd, check=False):
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True,
                       encoding='utf-8', errors='replace')
    if check and r.returncode != 0:
        raise RuntimeError(cmd)
    return (r.stdout or '') + (r.stderr or '')


def md5_local(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def md5_remote(path):
    out = sh(f"su -c 'md5sum {path} 2>/dev/null'")
    return out.split(' ')[0].strip() if out.strip() else ''


def force_stop():
    sh(f'am force-stop {PKG}')
    print('已退出游戏')


def push_tables():
    names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'),
                           encoding='utf-8'))
    ok = miss = bad = 0
    for tn, h in sorted(names.items()):
        src = os.path.join(ROOT, 'out', f'{tn}.bin')
        if not os.path.exists(src):
            miss += 1
            continue
        tmp = f'/data/local/tmp/t_{h}'
        subprocess.run([ADB, 'push', src, tmp], capture_output=True)
        sh(f"su -c 'cp {tmp} {CACHE}/{h}; chown {OWNER} {CACHE}/{h}; "
           f"chmod 600 {CACHE}/{h}; rm -f {tmp}'")
        if md5_remote(f'{CACHE}/{h}') == md5_local(src):
            ok += 1
        else:
            bad += 1
    print(f'主表: 成功 {ok}, 失败 {bad}, 本地缺失 {miss}')
    return bad == 0 and ok > 0


def push_story():
    out = os.path.join(ROOT, 'lw_work', 'story_out')
    if not os.path.isdir(out):
        print('剧情包: 无 story_out 目录，跳过')
        return True
    ok = bad = 0
    for fn in os.listdir(out):
        if not fn.endswith('__data'):
            continue
        a, b, _ = fn.split('__')
        src = os.path.join(out, fn)
        tmp = f'/data/local/tmp/s_{a}'
        subprocess.run([ADB, 'push', src, tmp], capture_output=True)
        tgt = f'{UC}/{a}/{b}/__data'
        sh(f"su -c 'cp {tmp} {tgt}; chown {OWNER} {tgt}; chmod 660 {tgt}; rm -f {tmp}'")
        if md5_remote(tgt) == md5_local(src):
            ok += 1
        else:
            bad += 1
    print(f'剧情包: 成功 {ok}, 失败 {bad}')
    return bad == 0 and ok > 0


def check():
    names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'),
                           encoding='utf-8'))
    same = diff = miss = 0
    for tn, h in names.items():
        src = os.path.join(ROOT, 'out', f'{tn}.bin')
        if not os.path.exists(src):
            continue
        d = md5_remote(f'{CACHE}/{h}')
        if not d:
            miss += 1
        elif d == md5_local(src):
            same += 1
        else:
            diff += 1
    print(f'主表状态: 中文版 {same}, 已被覆盖 {diff}, 读取失败 {miss}')
    # 剧情包：优先检查简体新版目录，其次旧的繁体目录
    out = os.path.join(ROOT, 'lw_work', 'story_sc_out')
    if not os.path.isdir(out):
        out = os.path.join(ROOT, 'lw_work', 'story_out')
    if os.path.isdir(out):
        s = b = 0
        for fn in os.listdir(out):
            if not fn.endswith('__data'):
                continue
            a, bb, _ = fn.split('__')
            src = os.path.join(out, fn)
            if md5_remote(f"{UC}/{a}/{bb}/__data") == md5_local(src):
                s += 1
            else:
                b += 1
        print(f'剧情包状态: 中文版 {s}, 已失效 {b}')


def main():
    what = sys.argv[1] if len(sys.argv) > 1 else 'all'
    if what == 'check':
        check()
        return
    force_stop()
    if what in ('all', 'tables'):
        push_tables()
    if what in ('all', 'story'):
        push_story()
    print('\n完成。请手动启动游戏（或 adb shell am start -n %s/com.google.firebase.MessagingUnityPlayerActivity）' % PKG)
    check()


if __name__ == '__main__':
    main()
