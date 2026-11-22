#!/usr/bin/env python3
"""把日服原始 master 表恢复回去（从 dumped/ 重新加密后推送）。

用法：
  python lw_restore.py                 # 恢复全部 212 张表
  python lw_restore.py Mission Voice   # 只恢复指定表
"""
import os, sys, glob, json, subprocess, msgpack, argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import encrypt
from lw_patch import resolve, push, ADB, PKG

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'out_orig')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tables', nargs='*')
    args = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
    todo = []
    if args.tables:
        for t in args.tables:
            h, name = resolve(t)
            todo.append((name, h))
    else:
        for name, h in names.items():
            if os.path.exists(os.path.join(ROOT, 'dumped', h + '.msgpack')):
                todo.append((name, h))
    made = []
    for name, h in todo:
        blob = open(os.path.join(ROOT, 'dumped', h + '.msgpack'), 'rb').read()
        p = os.path.join(OUT, name + '.bin')
        open(p, 'wb').write(encrypt(blob))
        made.append((name, h, p, 0))
    print(f'恢复 {len(made)} 张表')
    push(made)


if __name__ == '__main__':
    main()
