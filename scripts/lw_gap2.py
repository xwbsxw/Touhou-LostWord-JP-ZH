# -*- coding: utf-8 -*-
"""把「剩余未译」按「玩家可见性」× 「汉化包能不能帮上忙」交叉分类。

桶：
  A 日服独有行（国际服表里根本没有这行）      -> 任何中文源都覆盖不到
  B 行在，但汉化包该格没有中文（国际服显示英文） -> 汉化包帮不上，需要真翻译
  C 行在且有中文，只是被我的闸门挡掉            -> 复核后可直接放行
"""
import os, re, json, msgpack
from lw_visible import visible_field, is_internal, KANA

ROOT = os.path.dirname(os.path.abspath(__file__))
PATCH_DIR = os.path.join(ROOT, 'dl', 'ext', 'lwlocal', 'dec')
JP_DIR = os.path.join(ROOT, 'dumped')
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
trans = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')


def load(p):
    try:
        return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None


rows = []
T = {'vis': [0, 0, 0], 'int': [0, 0, 0], 'hid': [0, 0, 0]}
for tname, h in NAMES.items():
    jp = os.path.join(JP_DIR, h + '.msgpack')
    if not os.path.exists(jp):
        continue
    J = load(jp)
    P = load(os.path.join(PATCH_DIR, h + '.msgpack'))
    tr = trans.get(tname, {})
    v = [0, 0, 0]
    for rid, jr in J.items():
        if not isinstance(jr, list):
            continue
        trr = tr.get(str(rid), {})
        pr = P.get(rid) if P else None
        for i, x in enumerate(jr):
            if not isinstance(x, str) or not KANA.search(x) or str(i) in trr:
                continue
            if pr is None:
                k = 0
            elif i < len(pr) and isinstance(pr[i], str) and HAN.search(pr[i]) and not KANA.search(pr[i]) and pr[i].strip() != x.strip():
                k = 2
            else:
                k = 1
            if not visible_field(tname, i):
                T['hid'][k] += 1
            elif is_internal(x):
                T['int'][k] += 1
            else:
                T['vis'][k] += 1
                v[k] += 1
    if any(v):
        rows.append((tname, v))

rows.sort(key=lambda r: -sum(r[1]))
print(f'{"表":22s} {"A日服独有":>9s} {"B无中文":>9s} {"C可放行":>8s} {"可见小计":>9s}')
for t, v in rows[:20]:
    print(f'{t:22s} {v[0]:>9d} {v[1]:>9d} {v[2]:>8d} {sum(v):>9d}')
print('-' * 62)
tv = T['vis']
print(f'{"可见待译 合计":22s} {tv[0]:>9d} {tv[1]:>9d} {tv[2]:>8d} {sum(tv):>9d}')
print()
print(f'内部调试串     A{tv[0] and T["int"][0] or T["int"][0]:>9d} B{T["int"][1]:>9d} C{T["int"][2]:>8d} 小计 {sum(T["int"])}')
print(f'隐藏字段       A{T["hid"][0]:>9d} B{T["hid"][1]:>9d} C{T["hid"][2]:>8d} 小计 {sum(T["hid"])}')
print(f'三类总计       A{sum(x[0] for x in T.values()):>9d} B{sum(x[1] for x in T.values()):>9d} C{sum(x[2] for x in T.values()):>8d}')
