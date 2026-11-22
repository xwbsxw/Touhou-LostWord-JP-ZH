# -*- coding: utf-8 -*-
"""把剩余待译串逐个丢进 tr_one，看是哪一族没接住。"""
import os, json, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lw_rules as R

w = json.load(open('lw_work/work_visible.json', encoding='utf-8'))
FIELDS = [('Bullet', '2'), ('Skill', '2'), ('Spellcard', '3'), ('Shot', '3'),
          ('ValuePackShop', '5'), ('Mission', '2'), ('VoiceSet', '3'), ('Enemy', '3')]

for tbl, fi in FIELDS:
    items = w.get(tbl, {}).get(fi, [])
    if not items:
        continue
    print(f'===== {tbl}[{fi}]  唯一 {len(items)} =====')
    for s, n in items[:12]:
        t = R.tr_one(s)
        mark = 'OK ' if t else 'MISS'
        if t and R.KANA.search(t):
            mark = 'KANA'
        print(f'  [{mark}] {s[:72]!r}')
        if t:
            print(f'         -> {t[:72]!r}')
    print()
