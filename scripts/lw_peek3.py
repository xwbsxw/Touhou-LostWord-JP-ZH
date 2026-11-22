# -*- coding: utf-8 -*-
"""看「国服无此行」「国服其他」这两桶到底是不是玩家可见的新内容。"""
import os, re, json, msgpack
from lw_visible import visible_field, is_internal

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
trans = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

buckets = {'国服无此行': [], '国服其他': []}
for tname, h in NAMES.items():
    jp = os.path.join(ROOT, 'dumped', h + '.msgpack')
    cp = os.path.join(ROOT, 'lw_work', 'dump_cn', h + '.msgpack')
    if not os.path.exists(jp):
        continue
    J = msgpack.unpackb(open(jp, 'rb').read(), raw=False, strict_map_key=False)
    C = msgpack.unpackb(open(cp, 'rb').read(), raw=False, strict_map_key=False) if os.path.exists(cp) else {}
    tr = trans.get(tname, {})
    for rid, jr in J.items():
        if not isinstance(jr, list):
            continue
        trr = tr.get(str(rid), {})
        for i, jv in enumerate(jr):
            if not isinstance(jv, str) or not KANA.search(jv) or str(i) in trr:
                continue
            if not visible_field(tname, i) or is_internal(jv):
                continue
            cr = C.get(rid)
            cv = cr[i] if isinstance(cr, list) and i < len(cr) else None
            if not isinstance(cv, str) or not cv.strip():
                k = '国服无此行'
            elif HAN.search(cv) and not KANA.search(cv):
                continue
            elif cv.strip() == jv.strip():
                continue
            else:
                k = '国服其他'
            if len(buckets[k]) < 300:
                buckets[k].append((tname, i, rid, jv, cv))

for k, L in buckets.items():
    print(f'===== {k}  共采样 {len(L)} =====')
    for t, i, rid, jv, cv in L[:22]:
        print(f'  {t}[{i}] {rid}')
        print(f'      日: {jv[:64]!r}')
        print(f'      国: {str(cv)[:64]!r}')
    print()
