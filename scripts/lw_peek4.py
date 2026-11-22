# -*- coding: utf-8 -*-
"""打印「真正待译」里各表各字段的样例，用于设计规则。"""
import json, sys

w = json.load(open('lw_work/work_visible.json', encoding='utf-8'))
rep = json.load(open('lw_work/visible_report.json', encoding='utf-8'))
targets = sys.argv[1:] or [k for k, _ in list(rep['per_field'].items())[:14]]

for key in targets:
    tbl, fi = key[:-1].split('[')[0], int(key[:-1].split('[')[1])
    items = w.get(tbl, {}).get(str(fi), [])
    print(f'===== {key}  唯一串 {len(items)}  字段总数 {sum(n for _, n in items)} =====')
    for s, n in items[:10]:
        print(f'  x{n:<3}{s[:96]!r}')
    print()
