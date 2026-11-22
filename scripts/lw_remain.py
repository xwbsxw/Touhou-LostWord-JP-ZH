# -*- coding: utf-8 -*-
"""导出剩余待译的唯一串清单（按出现次数降序），供人工补译。"""
import os, json, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
w = json.load(open(os.path.join(ROOT, 'lw_work', 'work_visible.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u30ff]')

per = collections.Counter()
where = collections.defaultdict(set)
for tbl, fields in w.items():
    for fi, items in fields.items():
        for s, n in items:
            per[s] += n
            where[s].add(f'{tbl}[{fi}]')

rows = sorted(per.items(), key=lambda kv: -kv[1])
json.dump({s: n for s, n in rows},
          open(os.path.join(ROOT, 'lw_work', 'remain_list.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)

print(f'唯一待译串 {len(rows)}  覆盖字段 {sum(n for _, n in rows)}')
print()
for s, n in rows[:120]:
    tabs = ','.join(sorted(where[s]))[:34]
    print(f'{n:>4}  {tabs:34s} {s[:90]}')
