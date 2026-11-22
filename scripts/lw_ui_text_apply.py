# -*- coding: utf-8 -*-
"""把第二批翻译写入普通 Text.m_Text。

基底优先用 lw_work/ui_out（已含 jpText 翻译），否则用 jpuc3 原包。
输出 lw_work/ui_text_out。
"""
import os, sys, json, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_ui_sc import UI_SC
from lw_ui_text_sc import UI_TEXT_SC

SRC = os.path.join(ROOT, 'lw_work/jpuc3')
PREV = os.path.join(ROOT, 'lw_work/ui_out')
OUT = os.path.join(ROOT, 'lw_work/ui_text_out')
todo = json.load(open(os.path.join(ROOT, 'lw_work/ui_text_todo.json'), encoding='utf-8'))

COMBINED = dict(UI_SC)
COMBINED.update(UI_TEXT_SC)

write = '--write' in sys.argv
hit = miss = 0
by = collections.defaultdict(dict)
for r in todo:
    sc = COMBINED.get(r['m_Text'])
    if sc is None:
        miss += 1
        continue
    hit += 1
    by[(r['a'], r['b'])][r['path_id']] = sc

print(f'待处理 {len(todo)} 条；已译 {hit} ({hit/len(todo)*100:.1f}%)；未覆盖 {miss}')
print(f'涉及 {len(by)} 个包')
if not write:
    print('（未写入，加 --write）')
    sys.exit()

os.makedirs(OUT, exist_ok=True)
made = total = 0
for (a, b), want in by.items():
    prev = os.path.join(PREV, f'{a}__{b}__data')
    src = prev if os.path.exists(prev) else os.path.join(SRC, a, b, '__data')
    if not os.path.exists(src):
        continue
    env = UnityPy.load(src)
    n = 0
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        sc = want.get(o.path_id)
        if sc is None:
            continue
        t = o.read_typetree()
        t['m_Text'] = sc
        o.save_typetree(t)
        n += 1
    if not n:
        continue
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    made += 1
    total += n
    print(f'  {a[:10]}…  {n:>3} 条  -> {len(raw)} B')

print(f'\n完成：{made} 个包 / {total} 条 -> {OUT}')
