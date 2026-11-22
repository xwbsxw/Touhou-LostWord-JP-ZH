# -*- coding: utf-8 -*-
"""导出日服 3 个剧情包的台词，生成待译清单。
输出 lw_work/story_todo.json :
  [{id, bundle(a/b), pid, name, text, text_tw(null)}]
同时统计出现的说话人名（m_name），人名也要译，单独列一份。
"""
import os, sys, json, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jp_story.json')

rows = json.load(open(SRC, encoding='utf-8'))
print(f'原始台词 {len(rows)} 条')

# 过滤：m_text 为空的已在抽取阶段剔除；这里只保留有实际内容的
todo = []
names = collections.Counter()
for i, r in enumerate(rows):
    txt = r['text']
    if not txt.strip():
        continue
    nm = (r.get('name') or '').strip()
    if nm:
        names[nm] += 1
    todo.append({
        'id': i,
        'bundle': f"{r['a']}/{r['b']}",
        'pid': r['pid'],
        'name': nm,
        'text': txt,
        'text_tw': None,
    })

print(f'待译 {len(todo)} 条')
out = os.path.join(ROOT, 'lw_work', 'story_todo.json')
json.dump(todo, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('->', out)

print(f'\n说话人名 {len(names)} 个:')
for k, v in names.most_common():
    print(f'  {v:>4}  {k}')

# 控制码统计（必须原样保留）
codes = collections.Counter()
for t in todo:
    for m in re.finditer(r'\x1b?c\d{2}', t['text']):
        codes[m.group(0)] += 1
    for m in re.finditer(r'\{[^}]{1,12}\}', t['text']):
        codes[m.group(0)] += 1
    for m in re.finditer(r'<[^>]{1,20}>', t['text']):
        codes[m.group(0)] += 1
print(f'\n富文本/控制码 {len(codes)} 种:')
for k, v in codes.most_common(20):
    print(f'  {v:>4}  {k!r}')
