# -*- coding: utf-8 -*-
"""把剧情台词从繁中转为简体，重新写回日服剧情包。

输入：lw_work/story_tw.json（text_tw / name_tw 为繁中）
输出：lw_work/story_out/（简体版 bundle）
"""
import os, sys, json, collections
import UnityPy
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc')
OUT = os.path.join(ROOT, 'lw_work', 'story_out')
cc = OpenCC('t2s')

rows = json.load(open(os.path.join(ROOT, 'lw_work', 'story_tw.json'), encoding='utf-8'))
print(f'台词 {len(rows)} 条')

# 简体化（就地更新 json，同时统计变化）
changed = 0
for r in rows:
    sc = cc.convert(r['text_tw'])
    if sc != r['text_tw']:
        changed += 1
    r['text_sc'] = sc
    r['name_sc'] = cc.convert(r['name_tw'])
print(f'转简体后发生变化 {changed} 条')

json.dump(rows, open(os.path.join(ROOT, 'lw_work', 'story_sc.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)

by_b = collections.defaultdict(dict)
for r in rows:
    by_b[r['bundle']][r['pid']] = r

os.makedirs(OUT, exist_ok=True)
for bundle, byp in by_b.items():
    a, b = bundle.split('/')
    f = os.path.join(SRC, a, b, '__data')
    if not os.path.exists(f):
        # 已推送过中文版的，用 story_out 里的作基底
        f = os.path.join(OUT, f'{a}__{b}__data')
    env = UnityPy.load(f)
    hit = 0
    for obj in env.objects:
        rec = byp.get(obj.path_id)
        if rec is None:
            continue
        tree = obj.read_typetree()
        tree['m_text'] = rec['text_sc']
        if tree.get('m_name'):
            tree['m_name'] = rec['name_sc']
        obj.save_typetree(tree)
        hit += 1
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    print(f'  {a[:10]}…  写回 {hit} 条  {len(raw)} B')

# 抽样
print('\n=== 简体抽样 ===')
for r in rows[:4]:
    print(f'  [{r["name_sc"]}] {r["text_sc"][:56]!r}')
