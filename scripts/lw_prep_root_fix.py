# -*- coding: utf-8 -*-
"""为「极短 root 窗口」准备最小动作脚本。

核心思路：root 窗口内只做 chgrp/chmod（纯元数据，毫秒级），
把 132 个 UI bundle 目录与文件改成 ext_data_rw 组可写。
之后 shell 用户即可免 root 覆盖 __data，不受窗口时长限制。

产物：
  lw_work/rootfix/fix.sh     设备上执行的脚本（带进度标记，可反复续跑）
  lw_work/rootfix/pairs.txt  132 个 (A,B) 全键
"""
import os, sys, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'

# 从 jpuc3 的目录名拿到完整 A/B 键
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')

pairs = []
for d in ('ui_out', 'ui_text_out'):
    p = os.path.join(ROOT, 'lw_work', d)
    if not os.path.isdir(p):
        continue
    for fn in os.listdir(p):
        if not fn.endswith('__data'):
            continue
        a, b, _ = fn.split('__')
        if os.path.isdir(os.path.join(SRC, a, b)):
            pairs.append((a, b))

pairs = sorted(set(pairs))
print(f'目标目录 {len(pairs)} 个')

outdir = os.path.join(ROOT, 'lw_work', 'rootfix')
os.makedirs(outdir, exist_ok=True)

with open(os.path.join(outdir, 'pairs.txt'), 'w', encoding='utf-8') as f:
    for a, b in pairs:
        f.write(f'{a} {b}\n')

lines = ['#!/system/bin/sh',
         '# 由 lw_prep_root_fix.py 生成：只改权限，不搬数据',
         f'UC={UC}',
         'DONE=0']
for a, b in pairs:
    d = f'$UC/{a}/{b}'
    lines.append(f'[ -d "{d}" ] && chgrp ext_data_rw "{d}" 2>/dev/null; '
                 f'chmod 2770 "{d}" 2>/dev/null; '
                 f'chgrp ext_data_rw "{d}/__data" "{d}/__info" 2>/dev/null; '
                 f'chmod 660 "{d}/__data" "{d}/__info" 2>/dev/null; '
                 f'DONE=$((DONE+1))')
lines.append(f'echo "DIRS_PROCESSED=$DONE"')
# 顺带把 UnityCache 顶层与 Shared 也放开，方便以后
lines.append(f'chgrp ext_data_rw {UC} 2>/dev/null; chmod 2770 {UC} 2>/dev/null')
lines.append('echo FIX_DONE')

sh_path = os.path.join(outdir, 'fix.sh')
open(sh_path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
print(f'fix.sh 行数 {len(lines)}，大小 {os.path.getsize(sh_path)} B')

# 推送到设备（无需 root，/data/local/tmp 可写）
r = subprocess.run([ADB, 'shell', 'mkdir -p /data/local/tmp/lwfix'],
                   capture_output=True, encoding='utf-8', errors='replace')
pr = subprocess.run([ADB, 'push', sh_path, '/data/local/tmp/lwfix/fix.sh'],
                    capture_output=True, encoding='utf-8', errors='replace')
print('push fix.sh:', (pr.stdout or pr.stderr or '').strip()[:100])
subprocess.run([ADB, 'shell', 'chmod 755 /data/local/tmp/lwfix/fix.sh'],
               capture_output=True)
chk = subprocess.run([ADB, 'shell', 'ls -l /data/local/tmp/lwfix/fix.sh'],
                     capture_output=True, encoding='utf-8', errors='replace')
print('设备上:', (chk.stdout or '').strip())
