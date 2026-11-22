# -*- coding: utf-8 -*-
"""量化：日服剩余未译字段中，有多少是国际服汉化包「够不着」的。

分三桶：
  A 行不在汉化包里          -> 日服独有内容，任何中文源都覆盖不到
  B 行在，但该格没中文      -> 国际服自己也没翻（保持英文），需另找源
  C 行在且有中文却被闸门挡掉 -> 可人工复核后放行
"""
import os, re, json, msgpack
ROOT = os.path.dirname(os.path.abspath(__file__))
PATCH_DIR = os.path.join(ROOT, 'dl', 'ext', 'lwlocal', 'dec')
JP_DIR = os.path.join(ROOT, 'dumped')
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
trans = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))

KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
TAG = re.compile(r'</?([A-Za-z]+)')
PH = re.compile(r'\{(\d+)(?::[^{}]*)?\}')


def load(p):
    try:
        return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None


rows = []
tot = [0, 0, 0]
for tname, h in NAMES.items():
    jp = os.path.join(JP_DIR, h + '.msgpack')
    if not os.path.exists(jp):
        continue
    J = load(jp)
    P = load(os.path.join(PATCH_DIR, h + '.msgpack'))
    tr = trans.get(tname, {})
    a = b = c = 0
    for rid, jr in J.items():
        if not isinstance(jr, list):
            continue
        trr = tr.get(str(rid), {})
        pr = P.get(rid) if P else None
        for i, v in enumerate(jr):
            if not isinstance(v, str) or not KANA.search(v):
                continue
            if str(i) in trr:
                continue
            if pr is None:
                a += 1
            elif i < len(pr) and isinstance(pr[i], str) and HAN.search(pr[i]) and not KANA.search(pr[i]) and pr[i].strip() != v.strip():
                c += 1
            else:
                b += 1
    if a + b + c:
        rows.append((tname, a, b, c))
        tot[0] += a; tot[1] += b; tot[2] += c

rows.sort(key=lambda x: -(x[1] + x[2] + x[3]))
print(f'{"表":24s} {"A日服独有":>10s} {"B无中文":>10s} {"C被闸门挡":>10s}')
for t, a, b, c in rows[:26]:
    print(f'{t:24s} {a:>10d} {b:>10d} {c:>10d}')
print('-' * 58)
print(f'{"合计":24s} {tot[0]:>10d} {tot[1]:>10d} {tot[2]:>10d}')
print(f'剩余未译总数 = {sum(tot)}')
