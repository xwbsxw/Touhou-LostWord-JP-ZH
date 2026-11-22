# -*- coding: utf-8 -*-
"""归纳 s2twp 造成的用词失真，生成精确的「回退替换表」。

方法：对每个 原文 vs t2s(繁中) 不一致的字段，取最长公共前缀/后缀，
中间不同的部分作为 (回转词 -> 原词) 候选对，聚合统计词频。
输出 lw_work/tw_artifacts.json
"""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
CN_DIR = os.path.join(ROOT, 'dev_cn', 'cache', 'cncache')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
cc = OpenCC('t2s')
tw = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_cn_tw.json'), encoding='utf-8'))


def mid_diff(a, b):
    """返回 (a中与b不同的片段, b中与a不同的片段)"""
    i = 0
    n = min(len(a), len(b))
    while i < n and a[i] == b[i]:
        i += 1
    j = 0
    while j < n - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    return a[i:len(a) - j], b[i:len(b) - j]


pairs = collections.Counter()
total = diff = 0

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
                continue
            diff += 1
            o, r = mid_diff(orig, back)
            # 只在片段较短时计入（长片段多半是排版差异，不做替换）
            if 0 < len(o) <= 8 and 0 < len(r) <= 8:
                pairs[(r, o)] += 1

print(f'比对 {total} 字段，差异 {diff} ({diff/max(1,total)*100:.2f}%)')
print(f'\n可归纳片段对 {len(pairs)} 种，覆盖 {sum(pairs.values())} 处差异')

top = pairs.most_common(60)
print('\n=== 高频替换对（回转词 -> 原词）===')
for (r, o), c in top:
    print(f'  {c:>6}  {r!r} -> {o!r}')

out = {f'{r}\t{o}': c for (r, o), c in pairs.most_common(400)}
json.dump({'total': total, 'diff': diff,
           'pairs': [[r, o, c] for (r, o), c in pairs.most_common(400)]},
          open(os.path.join(ROOT, 'lw_work', 'tw_artifacts.json'), 'w',
               encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n已保存前 400 对 -> lw_work/tw_artifacts.json')
