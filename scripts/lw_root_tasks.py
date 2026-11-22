# -*- coding: utf-8 -*-
"""root 窗口内的一次性多任务：
  1) 权限加固：让 shell 以后免 root 就能写 UnityCache 与主表 cache
  2) 核对主表：与本地 out/*.bin 比对 md5，判断是否被重置回日文
  3) 打印结果
尽量把耗时的动作放在最后，先把权限开通（最重要）。
"""
import os, sys, json, hashlib, subprocess

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
CACHE = f'/data/data/{PKG}/files/cache'
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


def main():
    who = sh("su -c id")
    if 'uid=0' not in who:
        print('没有 root:', who[:80])
        return 1
    print('root OK:', who[:50])

    # ---------- 1. 权限加固 ----------
    print('\n=== 1. 权限加固 ===')
    # 主表 cache 目录：组改成 ext_data_rw 并组可写，shell 以后能读写
    sh(f"su -c 'chgrp -R ext_data_rw {CACHE} 2>/dev/null; "
       f"chmod -R 770 {CACHE} 2>/dev/null; "
       f"chmod 2770 {CACHE} 2>/dev/null; echo cache_done'")
    # UnityCache 整个树：组 ext_data_rw + 组可写（目录 2770，文件 660）
    sh(f"su -c 'find {UC} -maxdepth 0 -exec chgrp ext_data_rw {{}} \\; 2>/dev/null'")
    sh(f"su -c 'find {UC} -type d -exec chmod 2770 {{}} \\; 2>/dev/null'")
    sh(f"su -c 'find {UC} -type f -exec chmod 660 {{}} \\; 2>/dev/null'")
    sh(f"su -c 'find {UC} -type f -exec chgrp ext_data_rw {{}} \\; 2>/dev/null'")
    print('  已完成 chgrp/chmod')

    # 验证：shell 能否直接读主表
    t = sh(f"ls {CACHE} 2>&1 | head -2")
    print(f'  shell 读主表: {t[:70]}')

    # ---------- 2. 核对主表 ----------
    print('\n=== 2. 主表核对 ===')
    names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
    same = diff = miss = 0
    diffs = []
    for tn, h in sorted(names.items()):
        lp = os.path.join(ROOT, 'out', f'{tn}.bin')
        if not os.path.exists(lp):
            continue
        got = sh(f"su -c 'md5sum {CACHE}/{h} 2>/dev/null'").split(' ')[0]
        if not got:
            miss += 1
            continue
        if got == md5_local(lp):
            same += 1
        else:
            diff += 1
            diffs.append(tn)
    print(f'  中文版 {same}, 已被重置 {diff}, 读不到 {miss}')
    if diffs:
        print(f'  被重置的表（前15）: {diffs[:15]}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
