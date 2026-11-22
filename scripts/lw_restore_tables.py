# -*- coding: utf-8 -*-
"""把设备上的主表还原成日文原版（从 dumped/ 重新加密），用于二分定位黑屏。

用法: python lw_restore_tables.py [表名1 表名2 ...]
不带参数 = 还原 out/ 里全部 86 张表。
"""
import os, sys, json, hashlib, subprocess, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import encrypt

ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
CACHE = f'/data/data/{PKG}/files/cache'
OWNER = 'u0_a469:u0_a469'

names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

targets = sys.argv[1:] if len(sys.argv) > 1 else sorted(os.listdir(os.path.join(ROOT, 'out')))
targets = [t[:-4] for t in targets if t.endswith('.bin')]

ok = bad = miss = 0
for tn in targets:
    h = names.get(tn)
    if not h:
        continue
    src = os.path.join(ROOT, 'dumped', f'{h}.msgpack')
    if not os.path.exists(src):
        miss += 1
        continue
    raw = open(src, 'rb').read()
    blob = encrypt(raw)
    tmp_local = os.path.join(ROOT, 'lw_work', '_restore.bin')
    open(tmp_local, 'wb').write(blob)
    tmp = f'/data/local/tmp/r_{h}'
    subprocess.run([ADB, 'push', tmp_local, tmp], capture_output=True)
    subprocess.run([ADB, 'shell', f"su -c 'cp {tmp} {CACHE}/{h}; chown {OWNER} {CACHE}/{h}; "
                                  f"chmod 600 {CACHE}/{h}; rm -f {tmp}'"], capture_output=True)
    # md5 校验
    hl = hashlib.md5(blob).hexdigest()
    out = subprocess.run([ADB, 'shell', f"su -c 'md5sum {CACHE}/{h}'"],
                         capture_output=True, encoding='utf-8', errors='replace').stdout
    if out.split(' ')[0].strip() == hl:
        ok += 1
    else:
        bad += 1
os.remove(tmp_local)

print(f'还原日文原版主表: 成功 {ok}, 失败 {bad}, 缺失 {miss}')
