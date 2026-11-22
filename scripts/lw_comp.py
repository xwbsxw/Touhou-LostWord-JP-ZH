# -*- coding: utf-8 -*-
"""构建「组件词典」components.json：卡名 / 角色名 / 称号 / 短句。

来源两路：
  1) names_exact.json —— 国服对照挖出的整串名字（滤掉「[称号]名前」这种拼接条目）
  2) 从已译字段反向挖 —— 同一张表同一行同一格里，日文格 <-> 繁中格 成对提取
第 2 路是关键：它能挖出 names_exact 漏掉的卡名（歩く漢方薬）、角色简称（八雲藍）等，
有了这些原子词，Bullet/Shot 里「卡名_角色名 射擊A」这种复合名就能整串拼出来。
"""
import os, json, re, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
TRANS = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
NAME_EXACT = json.load(open(os.path.join(ROOT, 'lw_work', 'names_exact.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

comp = {}
stat = {'names_exact': 0, 'reverse': 0, 'drop_bracket': 0, 'drop_kana': 0, 'drop_nohan': 0}


def add(jp, tw, src):
    if not isinstance(jp, str) or not isinstance(tw, str):
        return
    jp, tw = jp.strip(), tw.strip()
    if not jp or not tw or jp == tw:
        return
    if not (1 <= len(jp) <= 22):
        return
    if '[' in tw or ']' in tw:
        stat['drop_bracket'] += 1
        return
    if KANA.search(tw):
        stat['drop_kana'] += 1
        return
    if not HAN.search(tw):
        stat['drop_nohan'] += 1
        return
    if jp in comp:
        return
    comp[jp] = tw
    stat[src] += 1


for k, v in NAME_EXACT.items():
    add(k, v, 'names_exact')

for tbl, h in NAMES.items():
    p = os.path.join(ROOT, 'dumped', h + '.msgpack')
    if not os.path.exists(p):
        continue
    J = msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    if not isinstance(J, dict):
        continue
    tr = TRANS.get(tbl, {})
    for rid, jr in J.items():
        if not isinstance(jr, list):
            continue
        t = tr.get(str(rid))
        if not t:
            continue
        for i, jv in enumerate(jr):
            tv = t.get(str(i))
            if tv:
                add(jv, tv, 'reverse')

json.dump(comp, open(os.path.join(ROOT, 'lw_work', 'components.json'), 'w', encoding='utf-8'),
          ensure_ascii=False)
print(f'组件词典 {len(comp)} 条  {stat}')
for probe in ('歩く漢方薬', '吉弔八千慧', '八雲藍', '妹の心、姉知らず',
              '野良幽霊、切捨て御免？', '八意永琳', 'ひろつらなりの代', '三つ星'):
    print(f'  {probe!r:26} -> {comp.get(probe)!r}')
