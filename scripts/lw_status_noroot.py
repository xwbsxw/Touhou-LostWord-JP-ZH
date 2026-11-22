# -*- coding: utf-8 -*-
"""无 root 状态下的真实状态核对：
  - 剧情包 / 字体包 / UI 包：直接 md5sum（UnityCache 可读）
  - 主表：无法读取（需 root），标记为未知
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'


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


def check_dir(label, local_dir):
    p = os.path.join(ROOT, 'lw_work', local_dir)
    if not os.path.isdir(p):
        print(f'{label}: 无本地产物')
        return
    ok = diff = miss = 0
    details = []
    for fn in sorted(os.listdir(p)):
        if not fn.endswith('__data'):
            continue
        a, b, _ = fn.split('__')
        lp = os.path.join(p, fn)
        want = md5_local(lp)
        got = sh(f'md5sum {UC}/{a}/{b}/__data 2>/dev/null').split(' ')[0]
        if not got:
            miss += 1
        elif got == want:
            ok += 1
        else:
            diff += 1
            details.append((a[:10], os.path.getsize(lp),
                            sh(f"ls -l {UC}/{a}/{b}/__data 2>/dev/null").split()[4]
                            if sh(f"ls -l {UC}/{a}/{b}/__data 2>/dev/null") else '?'))
    print(f'{label}: 一致 {ok}, 不一致 {diff}, 读不到 {miss}')
    for d in details[:6]:
        print('   差异', d)


check_dir('剧情包 story_sc_out', 'story_sc_out')
check_dir('字体包 font_out', 'font_out')
check_dir('UI包 ui_out', 'ui_out')
check_dir('UI包 ui_text_out', 'ui_text_out')
print('\n主表: 无法读取（需 root），状态未知')
