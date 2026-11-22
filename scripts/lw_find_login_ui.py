# -*- coding: utf-8 -*-
"""在整个缓存里搜「スキップ」「ログインボーナス」等关键词，
定位签到相关文本在哪些主表 / UI bundle 里。
"""
import os, sys, re, json, msgpack
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

KEYS = ['スキップ', 'ログインボーナス', 'ログイン', '受け取り', 'プレゼント']

def hit(s):
    return any(k in s for k in KEYS)

# 1. 主表（日文原版）
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
print('===== 主表命中 =====')
for tn, h in sorted(names.items()):
    p = os.path.join(ROOT, 'dumped', h + '.msgpack')
    if not os.path.exists(p):
        continue
    try:
        obj = msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        continue
    for k, row in obj.items():
        rows = row if isinstance(row, list) else [row]
        for i, v in enumerate(rows):
            if isinstance(v, str) and hit(v) and len(v) < 200:
                print(f'  {tn} id={k} f={i}: {v[:60]!r}')

# 2. UI bundle
print('\n===== UI bundle 命中 =====')
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')
cnt = 0
for a in sorted(os.listdir(SRC)):
    d = os.path.join(SRC, a)
    if not os.path.isdir(d):
        continue
    for b in os.listdir(d):
        fp = os.path.join(d, b, '__data')
        if not os.path.exists(fp):
            continue
        try:
            env = UnityPy.load(fp)
        except Exception:
            continue
        found = []
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            for kk, v in t.items():
                if isinstance(v, str) and hit(v) and len(v) < 200:
                    found.append((kk, v))
        if found:
            cnt += 1
            print(f'  {a[:10]}/{b[:8]}: {found[:4]}')
            if cnt > 12:
                print('  ... 省略')
                sys.exit()
