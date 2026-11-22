# -*- coding: utf-8 -*-
"""把 78 个 UI bundle 的 __info 改成失效状态，触发游戏重新下载官方原版。

原理：Unity 缓存校验要求 __info 里的 epoch == __data 的 mtime。
      改写 epoch 即可让缓存失效；__info 属组 ext_data_rw，shell 可写。

用法: python lw_invalidate.py [--dry]
"""
import os, sys, subprocess

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


def main():
    dry = '--dry' in sys.argv
    pairs = collect()
    print(f'目标 {len(pairs)} 个 bundle' + ('  [dry]' if dry else ''))

    # 分批，避免命令行过长
    ok = fail = 0
    BATCH = 25
    for i in range(0, len(pairs), BATCH):
        part = pairs[i:i + BATCH]
        cmds = []
        for a, b in part:
            info = f'{UC}/{a}/{b}/__info'
            cmds.append(f"printf -- '-1\\n1\\n1\\n__data\\n' > {info}")
        cmd = '; '.join(cmds)
        if dry:
            print(f'  [dry] batch {i//BATCH+1}: {len(part)} 个')
            continue
        out = sh(cmd)
        bad = out.count('denied') + out.count('Permission')
        if bad:
            fail += bad
            print(f'  batch {i//BATCH+1}: 有 {bad} 个失败')
        else:
            ok += len(part)
    if not dry:
        print(f'已失效 {ok} 个，失败 {fail}')

        # 抽查确认
        a, b = pairs[0]
        print(f'\n抽查 {a[:10]}:')
        print(sh(f'ls -l {UC}/{a}/{b}/__data; cat {UC}/{a}/{b}/__info'))


if __name__ == '__main__':
    main()
