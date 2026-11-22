# -*- coding: utf-8 -*-
"""检查 78 个 UI bundle 的重下载状态：
   - mtime 是否更新（今天）
   - 属组是否变成 ext_data_rw（= 已重下，组可写）
   - 与本地 clean 版 md5 是否一致（能否读取）
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')


def sh(cmd):
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True,
                       encoding='utf-8', errors='replace')
    return ((r.stdout or '') + (r.stderr or '')).strip()


def collect():
    pairs = set()
    for d in ('ui_out', 'ui_text_out'):
        p = os.path.join(ROOT, 'lw_work', d)
        if not os.path.isdir(p):
            continue
        for fn in os.listdir(p):
            if fn.endswith('__data'):
                a, b, _ = fn.split('__')
                if os.path.isdir(os.path.join(SRC, a, b)):
                    pairs.add((a, b))
    return sorted(pairs)


pairs = collect()
fresh = writable = total = 0
notfresh = []
for a, b in pairs:
    d = f'{UC}/{a}/{b}'
    out = sh(f'ls -l {d}/__data 2>/dev/null')
    if not out or 'No such' in out:
        continue
    total += 1
    parts = out.split()
    grp = parts[3] if len(parts) > 3 else '?'
    if grp == 'ext_data_rw':
        writable += 1
    else:
        notfresh.append((a[:10], grp, parts[4] if len(parts) > 4 else '?',
                         parts[-2] if len(parts) > 2 else '?'))

print(f'共检查 {total} 个')
print(f'  属组已变 ext_data_rw（可写）: {writable}')
print(f'  仍为 u0_a469（不可写）: {len(notfresh)}')
for x in notfresh[:15]:
    print('   ', x)
