# -*- coding: utf-8 -*-
"""看看还没译的 Bullet[1] / SkillEffect[1] 到底长什么样。"""
import os, re, json, msgpack
ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
trans = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')

for tname, fi, n in (('Bullet', 1, 26), ('SkillEffect', 1, 14)):
    h = NAMES[tname]
    jp = msgpack.unpackb(open(f'dumped/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
    C = msgpack.unpackb(open(f'lw_work/dump_cn/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
    tr = trans.get(tname, {})
    print(f'=== {tname}[{fi}] 未译样例（附国服同格） ===')
    c = 0
    for rid, jr in jp.items():
        if not isinstance(jr, list) or fi >= len(jr):
            continue
        v = jr[fi]
        if not isinstance(v, str) or not KANA.search(v) or str(fi) in tr.get(str(rid), {}):
            continue
        cr = C.get(rid)
        cv = cr[fi] if isinstance(cr, list) and fi < len(cr) else None
        print(f'  [{rid}] {v[:56]!r}')
        print(f'          国服: {str(cv)[:56]!r}')
        c += 1
        if c >= n:
            break
    print()
