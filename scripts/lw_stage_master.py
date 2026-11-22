# -*- coding: utf-8 -*-
"""预置主表到设备 /data/local/tmp/lwm/（按 hash 命名），
并生成 root 窗口用的 onefix.sh，窗口内一条命令完成恢复。

用法: python lw_stage_master.py
"""
import os, sys, json, subprocess, shutil

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
CACHE = f'/data/data/{PKG}/files/cache'
STAGE_LOCAL = os.path.join(ROOT, 'lw_work', 'master_stage')
STAGE_DEV = '/data/local/tmp/lwm'
OWNER = 'u0_a469:u0_a469'

names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

os.makedirs(STAGE_LOCAL, exist_ok=True)
pairs = []          # (hash, local_stage_path)
for tn, h in sorted(names.items()):
    src = os.path.join(ROOT, 'out', f'{tn}.bin')
    if not os.path.exists(src):
        continue
    dst = os.path.join(STAGE_LOCAL, h + '.bin')
    if not os.path.exists(dst) or os.path.getsize(dst) != os.path.getsize(src):
        shutil.copy(src, dst)
    pairs.append((h, dst))

total = sum(os.path.getsize(p) for _, p in pairs)
print(f'待预置 {len(pairs)} 张表，{total/1048576:.1f} MB')

subprocess.run([ADB, 'shell', f'mkdir -p {STAGE_DEV}'], capture_output=True)
ok = bad = 0
for i, (h, p) in enumerate(pairs, 1):
    r = subprocess.run([ADB, 'push', p, f'{STAGE_DEV}/{h}.bin'],
                       capture_output=True, encoding='utf-8', errors='replace')
    if r.returncode == 0:
        ok += 1
    else:
        bad += 1
        print(f'  {h[:8]} push 失败')
    if i % 20 == 0:
        print(f'  ...{i}/{len(pairs)}')
print(f'预置完成: 成功 {ok}, 失败 {bad}')

# 生成 onefix.sh
lines = ['#!/system/bin/sh',
         f'CACHE={CACHE}',
         f'STAGE={STAGE_DEV}',
         f'OWNER={OWNER}',
         '# 1) 放开主表目录权限，让 shell 以后免 root 可读写',
         'chgrp -R ext_data_rw $CACHE 2>/dev/null',
         'chmod -R 777 $CACHE 2>/dev/null',
         'chmod 2777 $CACHE 2>/dev/null',
         '# 2) 覆盖主表',
         'N=0',
         'for f in $STAGE/*.bin; do',
         '  B=$(basename $f .bin)',
         '  cp $f $CACHE/$B 2>/dev/null && N=$((N+1))',
         '  chown $OWNER $CACHE/$B 2>/dev/null',
         '  chmod 666 $CACHE/$B 2>/dev/null',
         'done',
         'echo "COPIED=$N"',
         '# 3) shell 可读性验证',
         'ls $CACHE | wc -l',
         'echo ONEFIX_DONE']
sh_path = os.path.join(ROOT, 'lw_work', 'master_stage', 'onefix.sh')
open(sh_path, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines) + '\n')
r = subprocess.run([ADB, 'push', sh_path, f'{STAGE_DEV}/onefix.sh'],
                   capture_output=True, encoding='utf-8', errors='replace')
subprocess.run([ADB, 'shell', f'chmod 755 {STAGE_DEV}/onefix.sh'], capture_output=True)
print('onefix.sh 已推送')
