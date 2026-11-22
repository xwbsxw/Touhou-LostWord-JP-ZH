# -*- coding: utf-8 -*-
"""检查 + 还原 UI 包。先检查设备上是否推过（md5 对比），再还原到原版。"""
import os, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
OWNER = 'u0_a469:u0_a469'

def sh(cmd):
    return subprocess.run([ADB, 'shell', cmd], capture_output=True,
                          encoding='utf-8', errors='replace').stdout

def md5_remote(path):
    return sh(f"su -c 'md5sum {path} 2>/dev/null'").split(' ')[0].strip()

# 收集 ui_out + ui_text_out 的包
pairs = {}
for d in ('ui_out', 'ui_text_out'):
    p = os.path.join(ROOT, 'lw_work', d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if fn.endswith('__data'):
            a, b, _ = fn.split('__')
            pairs[(a, b)] = os.path.join(p, fn)

print(f'UI 产物包 {len(pairs)} 个')

# 检查哪些推到了设备（与本地产物 md5 一致）
pushed = []
for (a, b), src in pairs.items():
    tgt = f'{UC}/{a}/{b}/__data'
    rmd5 = md5_remote(tgt)
    if not rmd5:
        continue
    if rmd5 == hashlib.md5(open(src, 'rb').read()).hexdigest():
        pushed.append((a, b))
print(f'推送到设备的（md5==产物）: {len(pushed)} 个')

# 还原这些到原版
ok = bad = 0
for a, b in pushed:
    src = os.path.join(ROOT, 'lw_work', 'jpuc3', a, b, '__data')
    if not os.path.exists(src):
        bad += 1; continue
    tmp = f'/data/local/tmp/u_{a}'
    subprocess.run([ADB, 'push', src, tmp], capture_output=True)
    tgt = f'{UC}/{a}/{b}/__data'
    sh(f"su -c 'cp {tmp} {tgt}; chown {OWNER} {tgt}; chmod 660 {tgt}; rm -f {tmp}'")
    if md5_remote(tgt) == hashlib.md5(open(src, 'rb').read()).hexdigest():
        ok += 1
    else:
        bad += 1
print(f'还原 UI 包: 成功 {ok}, 失败 {bad}')
