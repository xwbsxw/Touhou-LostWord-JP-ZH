# -*- coding: utf-8 -*-
"""抽样看：国际服汉化包里「没给中文」的那些格子，到底长什么样。"""
import os, re, sys, json, msgpack
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

tname = sys.argv[1] if len(sys.argv) > 1 else 'Bullet'
h = NAMES[tname]
jp = msgpack.unpackb(open(f'dumped/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
P = msgpack.unpackb(open(f'dl/ext/lwlocal/dec/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
C = msgpack.unpackb(open(f'lw_work/dump_cn/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)

print(f'表 {tname}  日服行 {len(jp)}  包行 {len(P)}  国服行 {len(C)}')
print(f'共同行 {len(set(jp) & set(P))}')
print(f'字段数对比: 日 {len(next(iter(jp.values())))}  包 {len(next(iter(P.values())))}  国 {len(next(iter(C.values())))}')
print()
showed = 0
for rid in sorted(set(jp) & set(P)):
    jr, pr = jp[rid], P[rid]
    if not isinstance(jr, list) or not isinstance(pr, list):
        continue
    for i in range(min(len(jr), len(pr))):
        jv, pv = jr[i], pr[i]
        if not isinstance(jv, str) or not KANA.search(jv):
            continue
        if isinstance(pv, str) and HAN.search(pv) and not KANA.search(pv) and pv.strip() != jv.strip():
            continue
        cr = C.get(rid)
        cv = cr[i] if isinstance(cr, list) and i < len(cr) else None
        print(f'[{rid}.{i}]')
        print(f'   日 : {jv[:70]!r}')
        print(f'   包 : {pv[:70]!r}')
        print(f'   国 : {str(cv)[:70]!r}')
        showed += 1
        break
    if showed >= 14:
        break
