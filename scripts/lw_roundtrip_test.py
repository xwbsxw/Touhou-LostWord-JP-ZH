# -*- coding: utf-8 -*-
"""往返精度实测：国服官方简体原文  vs  (s2twp->t2s 回环结果)

trans_cn_tw.json 是「国服简体 --s2twp--> 繁体」的产物。
把它再用 t2s 转回简体，与国服官方原文逐字段比对，
统计失真率，用来判断「最终产物统一 t2s」这个方案是否可接受。
"""
import os, sys, json, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
CN_DIR = os.path.join(ROOT, 'dev_cn', 'cache', 'cncache')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

cc = OpenCC('t2s')
tw = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_cn_tw.json'), encoding='utf-8'))
print(f'trans_cn_tw: {len(tw)} 张表')

total = same = diff = 0
samples = []
per_table = {}

for table, rows in tw.items():
    h = names.get(table)
    if not h:
        continue
    p = os.path.join(CN_DIR, h)
    if not os.path.exists(p):
        continue
    try:
        obj = msgpack.unpackb(decrypt(open(p, 'rb').read()),
                              raw=False, strict_map_key=False)
    except Exception:
        continue
    t_same = t_diff = 0
    for rid, fields in rows.items():
        key = int(rid) if str(rid).lstrip('-').isdigit() else rid
        row = obj.get(key)
        if not isinstance(row, (list, tuple)):
            continue
        for idx, trad in fields.items():
            i = int(idx)
            if i >= len(row):
                continue
            orig = row[i]
            if not isinstance(orig, str) or not orig.strip():
                continue
            back = cc.convert(trad)
            total += 1
            if back == orig:
                same += 1
                t_same += 1
            else:
                diff += 1
                t_diff += 1
                if len(samples) < 25:
                    samples.append((table, rid, idx, orig, trad, back))
    if t_same + t_diff:
        per_table[table] = (t_same, t_diff)

print(f'\n总比对字段: {total}')
print(f'  完全一致: {same}  ({same/max(1,total)*100:.2f}%)')
print(f'  存在差异: {diff}  ({diff/max(1,total)*100:.2f}%)')

print('\n=== 差异抽样（原文 / 繁中 / 回转简中）===')
for t, r, i, o, tr, b in samples:
    print(f'  [{t} {r}.{i}]')
    print(f'    原文: {o[:60]}')
    print(f'    回转: {b[:60]}')

print('\n=== 失真最多的表 ===')
for t, (s, d) in sorted(per_table.items(), key=lambda x: -x[1][1])[:10]:
    print(f'  {t:24} 一致 {s:>6} / 差异 {d:>5}')
