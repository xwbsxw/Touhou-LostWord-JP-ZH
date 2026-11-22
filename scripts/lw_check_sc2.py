# -*- coding: utf-8 -*-
"""精确质量检测（只看「已翻译」的格子）：
  A. 已翻译但仍含简体字  -> OpenCC s2t 转换后有变化
  B. 已翻译但仍含日文新字体(転/戦/独/弾…) -> OpenCC 不管，需人工映射
  C. 仍是未翻译日文（含假名）-> 单独统计
"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, 'lw_work', 'jpcache', 'jpcache')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
H2N = {v: k for k, v in names.items()}
CC = OpenCC('s2t')
KANA = re.compile(r'[\u3040-\u30ff]')
JA = set('転戦鋭郷変実対経続図発亜圧応単団拡気帰広済帯剤摂桜検様撃歴渉満焼状独猟県総緑縁聴脳芸覧観訳証読鉄闘隣霊駅竜塩圏絵薬説楽権歳覚')

sc = collections.Counter(); ja = collections.Counter(); jp = collections.Counter()
sc_e = collections.defaultdict(list); ja_e = collections.defaultdict(list)
tot_tr = 0

for fn in os.listdir(CACHE):
    try:
        obj = msgpack.unpackb(decrypt(open(os.path.join(CACHE, fn), 'rb').read()),
                              raw=False, strict_map_key=False)
    except Exception:
        continue
    if not isinstance(obj, dict):
        continue
    tn = H2N.get(fn, fn[:8])
    for rid, row in obj.items():
        if not isinstance(row, (list, tuple)):
            continue
        for i, v in enumerate(row):
            if not isinstance(v, str) or not v:
                continue
            if KANA.search(v):
                jp[tn] += 1
                continue
            tot_tr += 1
            if CC.convert(v) != v:
                sc[tn] += 1
                if len(sc_e[tn]) < 3:
                    sc_e[tn].append(f'[{i}]id={rid}: {v[:46]}')
            if JA & set(v):
                ja[tn] += 1
                if len(ja_e[tn]) < 3:
                    ja_e[tn].append(f'[{i}]id={rid}: {v[:46]}')

print(f'已翻译(无假名)格子 {tot_tr}')
print()
print(f'=== A. 已翻译但仍含简体字: {sum(sc.values())} 个字段 / {len(sc)} 张表 ===')
for tn, n in sc.most_common(10):
    print(f'{n:>6}  {tn}')
    for s in sc_e[tn]:
        print(f'          {s}')
print()
print(f'=== B. 已翻译但仍含日文新字体: {sum(ja.values())} 个字段 / {len(ja)} 张表 ===')
for tn, n in ja.most_common(10):
    print(f'{n:>6}  {tn}')
    for s in ja_e[tn]:
        print(f'          {s}')
print()
print(f'=== C. 仍是未翻译日文(含假名): {sum(jp.values())} 个字段 ===')
for tn, n in jp.most_common(8):
    print(f'{n:>6}  {tn}')
