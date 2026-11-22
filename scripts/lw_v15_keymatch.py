# -*- coding: utf-8 -*-
"""统计 v1.5 的 431 个资源包能在日服命中多少（按缓存键 A/B 比对）。

v1.5 bundles.json 每条有 device_rel = "Shared/<A>/<B>/__data"。
"""
import os, json, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
man = json.load(open(os.path.join(ROOT, 'dl/v15/bundles.json'), encoding='utf-8'))
jp = set()
with open(os.path.join(ROOT, 'lw_work/jp_uc_pairs.txt'), encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        if line:
            jp.add(line)

print(f'v1.5 资源包 {len(man)} 个；日服缓存 {len(jp)} 个 A/B 键')

hit = collections.Counter()
miss = collections.Counter()
hit_list, miss_list = [], []
for r in man:
    rel = r['device_rel']              # Shared/<A>/<B>/__data
    parts = rel.split('/')
    key = f'{parts[1]}/{parts[2]}'
    kind = r.get('kind', '?')
    if key in jp:
        hit[kind] += 1
        hit_list.append(r)
    else:
        miss[kind] += 1
        miss_list.append(r)

print(f'\n命中（日服已有同键）: {sum(hit.values())}')
for k, v in hit.most_common():
    print(f'   {k:12} {v}')
print(f'未命中（日服无此键）: {sum(miss.values())}')
for k, v in miss.most_common():
    print(f'   {k:12} {v}')

json.dump({'hit': hit_list, 'miss': miss_list},
          open(os.path.join(ROOT, 'lw_work/v15_keymatch.json'), 'w',
               encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n明细 -> lw_work/v15_keymatch.json')
