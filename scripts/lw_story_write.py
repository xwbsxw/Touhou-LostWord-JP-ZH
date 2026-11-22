# -*- coding: utf-8 -*-
"""把繁中译文写回日服剧情包（MessageOrder.m_text / m_name），输出到 lw_work/story_out/。

严格只改这两个字符串字段，其余 typetree 原样写回（read_typetree -> save_typetree）。
"""
import os, sys, json, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc')
OUT = os.path.join(ROOT, 'lw_work', 'story_out')

rows = json.load(open(os.path.join(ROOT, 'lw_work', 'story_tw.json'), encoding='utf-8'))
# 按 (bundle, pid) 索引
by_b = collections.defaultdict(dict)
for r in rows:
    by_b[r['bundle']][r['pid']] = r

print(f'待写回 {len(rows)} 条, 涉及 {len(by_b)} 个包')

os.makedirs(OUT, exist_ok=True)
stat = []
for bundle, byp in by_b.items():
    a, b = bundle.split('/')
    f = os.path.join(SRC, a, b, '__data')
    env = UnityPy.load(f)
    n_obj_before = len(env.objects)
    hit = 0
    for obj in env.objects:
        rec = byp.get(obj.path_id)
        if rec is None:
            continue
        tree = obj.read_typetree()
        if tree.get('m_text') != rec['text']:
            print(f'  ! {a[:8]} pid={obj.path_id} 原文不匹配，跳过')
            continue
        tree['m_text'] = rec['text_tw']
        if tree.get('m_name'):
            tree['m_name'] = rec['name_tw']
        obj.save_typetree(tree)
        hit += 1
    dst = os.path.join(OUT, f'{a}__{b}__data')
    with open(dst, 'wb') as fp:
        fp.write(env.file.save(packer='lz4'))
    stat.append({
        'bundle': bundle, 'wrote': hit, 'expect': len(byp),
        'obj_before': n_obj_before,
        'src_size': os.path.getsize(f), 'dst_size': os.path.getsize(dst),
    })
    print(f'  {a[:8]}…  写回 {hit}/{len(byp)}  '
          f'{os.path.getsize(f)} -> {os.path.getsize(dst)} B')

json.dump(stat, open(os.path.join(ROOT, 'lw_work', 'story_out_stat.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n完成 ->', OUT)
