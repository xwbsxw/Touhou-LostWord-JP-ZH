# -*- coding: utf-8 -*-
"""统计 out/*.bin 日文残留的去重情况，按表分类，估算真实翻译量。"""
import os, sys, re, json, msgpack, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

KANA = re.compile(r'[\u3040-\u30ff]')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

per_table = {}
grand_uniq = set()
grand_total = 0

for fn in sorted(os.listdir(os.path.join(ROOT, 'out'))):
    if not fn.endswith('.bin'):
        continue
    name = fn[:-4]
    obj = msgpack.unpackb(decrypt(open(os.path.join(ROOT, 'out', fn), 'rb').read()),
                          raw=False, strict_map_key=False)
    uniq = set()
    total = 0
    for k, row in obj.items():
        if not isinstance(row, list):
            continue
        for v in row:
            if isinstance(v, str) and KANA.search(v) and v.strip():
                total += 1
                uniq.add(v)
                grand_uniq.add(v)
    if total:
        per_table[name] = (total, len(uniq))
        grand_total += total

print(f'日文残留总 {grand_total} 处，去重后 {len(grand_uniq)} 条')
print(f'去重率 {(1-len(grand_uniq)/grand_total)*100:.1f}%\n')
print(f'{"表":28}{"残留":>8}{"去重":>8}')
for name, (t, u) in sorted(per_table.items(), key=lambda x: -x[1][0]):
    print(f'{name:28}{t:>8}{u:>8}')
