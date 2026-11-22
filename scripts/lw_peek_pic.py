# -*- coding: utf-8 -*-
"""看设备上 Picture 表 id 45..60 的原始字段，判断卡名到底是日文/繁体/简体。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, 'lw_work', 'jpcache', 'jpcache')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

for tbl in ('Picture', 'Spellcard'):
    h = names.get(tbl)
    if not h:
        continue
    p = os.path.join(CACHE, h)
    if not os.path.exists(p):
        print(f'{tbl}: 设备无此表')
        continue
    obj = msgpack.unpackb(decrypt(open(p, 'rb').read()), raw=False, strict_map_key=False)
    print(f'===== {tbl} ({len(obj)} 行) 设备实测 =====')
    for rid in sorted(obj.keys(), key=lambda x: (not isinstance(x, int), x))[:0]:
        pass
    ks = [k for k in obj.keys() if isinstance(k, int) and 45 <= k <= 60]
    for rid in sorted(ks):
        row = obj[rid]
        s = ' | '.join(str(x)[:24] for x in row[:5] if isinstance(x, str))
        print(f'  id={rid}: {s[:110]}')
    print()
