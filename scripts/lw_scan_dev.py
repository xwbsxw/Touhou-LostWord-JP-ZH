# -*- coding: utf-8 -*-
"""在设备缓存里定位「靠谱」这类简体串到底来自哪张表哪个字段。"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack, json

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, 'lw_work', 'jpcache', 'jpcache')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
H2N = {v: k for k, v in names.items()}
manifest = json.load(open(os.path.join(ROOT, 'out', '_manifest.json'), encoding='utf-8'))
OURS = set(manifest.values())

TARGETS = ['靠谱', '猫咪帮', '无法逃离', '血污地狱', '通行禁止']

ok = bad = 0
found = []
for p in sorted(glob.glob(os.path.join(CACHE, '*'))):
    h = os.path.basename(p)
    try:
        obj = msgpack.unpackb(decrypt(open(p, 'rb').read()), raw=False, strict_map_key=False)
    except Exception:
        bad += 1
        continue
    ok += 1
    tn = H2N.get(h, '(未知表)')
    if not isinstance(obj, dict):
        continue
    for rid, row in obj.items():
        if not isinstance(row, (list, tuple)):
            continue
        for i, v in enumerate(row):
            if isinstance(v, str) and any(t in v for t in TARGETS):
                found.append((tn, h, h in OURS, rid, i, v[:50]))

print(f'可解密 {ok} 张, 失败 {bad} 张')
print(f'命中 {len(found)} 处')
print()
for tn, h, ours, rid, i, v in found[:40]:
    tag = '我方已推' if ours else '★未推送'
    print(f'{tag}  {tn}[{i}] id={rid}  {v}')
