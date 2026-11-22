# -*- coding: utf-8 -*-
"""把界面对照表应用到 bundle 的 jpText，并报告覆盖率。

用法:
  python lw_ui_apply.py            # 只统计覆盖率
  python lw_ui_apply.py --write    # 生成改写后的 bundle 到 lw_work/ui_out
"""
import os, sys, json, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_ui_sc import UI_SC

SRC = os.path.join(ROOT, 'lw_work/jpuc3')
OUT = os.path.join(ROOT, 'lw_work/ui_out')
todo = json.load(open(os.path.join(ROOT, 'lw_work/ui_todo.json'), encoding='utf-8'))

write = '--write' in sys.argv

hit = 0
miss = collections.Counter()
by_bundle = collections.defaultdict(list)
for r in todo:
    sc = UI_SC.get(r['jpText'])
    if sc is None:
        miss[r['jpText']] += 1
        continue
    hit += 1
    by_bundle[(r['a'], r['b'])].append((r['path_id'], sc))

print(f'待译 {len(todo)} 条；已译 {hit} 条 ({hit/len(todo)*100:.1f}%)；未覆盖 {len(miss)} 种')
if miss:
    print('\n未覆盖（按出现次数）:')
    for s, n in miss.most_common(30):
        print(f'  x{n}  {s[:70]!r}')

print(f'\n涉及 {len(by_bundle)} 个包，{sum(len(v) for v in by_bundle.values())} 个对象')

if not write:
    print('\n（未写入。加 --write 生成 bundle）')
    sys.exit()

os.makedirs(OUT, exist_ok=True)
made = 0
total = 0
for (a, b), items in by_bundle.items():
    p = os.path.join(SRC, a, b, '__data')
    if not os.path.exists(p):
        print(f'  跳过（源不存在）{a[:8]}')
        continue
    env = UnityPy.load(p)
    want = dict(items)
    n = 0
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        sc = want.get(o.path_id)
        if sc is None:
            continue
        t = o.read_typetree()
        t['jpText'] = sc
        o.save_typetree(t)
        n += 1
    if not n:
        continue
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    made += 1
    total += n
    print(f'  {a[:10]}…  {n:>3} 条  {os.path.getsize(p)} -> {len(raw)} B')

print(f'\n完成：{made} 个包 / {total} 条字段 -> {OUT}')
