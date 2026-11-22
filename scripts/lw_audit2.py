# -*- coding: utf-8 -*-
"""精确分类主表残留：日文（含假名）vs 真繁体（不含假名但 t2s 变化）。"""
import os, sys, re, msgpack
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

T2S = OpenCC('t2s')
KANA = re.compile(r'[\u3040-\u30ff]')
CJK = re.compile(r'[\u4e00-\u9fff]')

def classify(s):
    if not isinstance(s, str) or not s.strip():
        return None
    if KANA.search(s):
        return 'ja'
    if CJK.search(s) and T2S.convert(s) != s:
        return 'trad'
    return None

tot = {'ja': 0, 'trad': 0}
per_table = {}
ja_samples = {}
trad_samples = {}

for fn in sorted(os.listdir(os.path.join(ROOT, 'out'))):
    if not fn.endswith('.bin'):
        continue
    try:
        obj = msgpack.unpackb(decrypt(open(os.path.join(ROOT, 'out', fn), 'rb').read()),
                              raw=False, strict_map_key=False)
    except Exception:
        continue
    c = {'ja': 0, 'trad': 0}
    for rid, row in obj.items():
        rows = row if isinstance(row, list) else [row]
        for i, v in enumerate(rows):
            r = classify(v)
            if r:
                c[r] += 1
                tot[r] += 1
                d = ja_samples if r == 'ja' else trad_samples
                d.setdefault(fn, [])
                if len(d[fn]) < 3:
                    d[fn].append((rid, i, v[:50]))
    if c['ja'] or c['trad']:
        per_table[fn] = c

print('=== 主表精确分类 ===')
print(f'真繁体(不含假名): {tot["trad"]}  日文(含假名): {tot["ja"]}')
print()
for fn, c in sorted(per_table.items(), key=lambda x: -(x[1]['trad'] + x[1]['ja'])):
    print(f'{fn:32} 繁体 {c["trad"]:>7}  日文 {c["ja"]:>6}')
