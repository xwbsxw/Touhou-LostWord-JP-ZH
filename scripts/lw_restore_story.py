# -*- coding: utf-8 -*-
"""把剧情包还原成日文原版（从 jpuc3），用于定位图鉴黑屏。"""
import os, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
OWNER = 'u0_a469:u0_a469'

out = os.path.join(ROOT, 'lw_work', 'story_sc_out')
pairs = []
for fn in os.listdir(out):
    if fn.endswith('__data'):
        a, b, _ = fn.split('__')
        pairs.append((a, b))
print(f'还原剧情包 {len(pairs)} 个')

ok = bad = 0
for a, b in pairs:
    src = os.path.join(ROOT, 'lw_work', 'jpuc3', a, b, '__data')
    if not os.path.exists(src):
        print('  无原版', a[:8]); bad += 1; continue
    tmp = f'/data/local/tmp/s_{a}'
    subprocess.run([ADB, 'push', src, tmp], capture_output=True)
    tgt = f'{UC}/{a}/{b}/__data'
    subprocess.run([ADB, 'shell',
                    f"su -c 'cp {tmp} {tgt}; chown {OWNER} {tgt}; chmod 660 {tgt}; rm -f {tmp}'"],
                   capture_output=True)
    hl = hashlib.md5(open(src, 'rb').read()).hexdigest()
    r = subprocess.run([ADB, 'shell', f"su -c 'md5sum {tgt}'"],
                       capture_output=True, encoding='utf-8').stdout
    if r.split(' ')[0].strip() == hl:
        ok += 1
    else:
        bad += 1
print(f'还原剧情包: 成功 {ok}, 失败 {bad}')
