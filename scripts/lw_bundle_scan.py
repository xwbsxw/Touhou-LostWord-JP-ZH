# -*- coding: utf-8 -*-
"""扫描汉化补丁的 345 个资源包，统计其中的文本字段：
- 中日韩汉字串 / 含假名串（=未替换的原文）
- 出现的 MonoBehaviour 脚本类名
用来验证「剧情文本是否存放在 bundle 的 MonoBehaviour 文本字段里」。
"""
import os, sys, re, json, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
BDIR = os.path.join(ROOT, 'dl', 'ext', 'lwlocal', 'bundles')

import UnityPy

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')


def walk_str(o, out):
    if isinstance(o, str):
        if len(o) >= 4:
            out.append(o)
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in ('m_Script', 'm_GameObject'):
                continue
            walk_str(v, out)
    elif isinstance(o, (list, tuple)):
        for v in o:
            walk_str(v, out)


keys = []
for a in sorted(os.listdir(BDIR)):
    pa = os.path.join(BDIR, a)
    if not os.path.isdir(pa):
        continue
    for b in os.listdir(pa):
        keys.append((a, b, os.path.join(pa, b, '__data')))

print(f'补丁包 {len(keys)} 个')

whole = collections.Counter()   # bundle -> 认作「文本」的串数
cls = collections.Counter()
samp = collections.defaultdict(list)
tot_han = tot_kana = 0

for i, (a, b, p) in enumerate(keys):
    if i % 40 == 0:
        print(f'  ... {i}/{len(keys)}  已见中文串 {tot_han}', flush=True)
    if not os.path.exists(p):
        continue
    try:
        env = UnityPy.load(p)
    except Exception:
        continue
    n = 0
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        try:
            tree = obj.read_typetree()
            d = obj.read()
        except Exception:
            continue
        try:
            sc = getattr(d, 'm_Script', None)
            name = sc.read().m_ClassName if sc else '?'
        except Exception:
            name = '?'
        cls[name] += 1
        strs = []
        walk_str(tree, strs)
        for s in strs:
            if HAN.search(s):
                n += 1
                tot_han += 1
                if KANA.search(s):
                    tot_kana += 1
        if strs and len(samp[a]) < 2:
            samp[a].append(strs[0][:60])
    if n:
        whole[a] = n

print(f'\n含中文文本的包 {len(whole)} 个，中文串合计 {tot_han}，其中仍含假名 {tot_kana}')
print('\n=== 顶层脚本类名 top 25 ===')
for k, v in cls.most_common(25):
    print(f'{v:>7}  {k}')
print('\n=== 中文串最多的包 top 12 ===')
for a, n in whole.most_common(12):
    print(f'{n:>7}  {a}')
    for s in samp[a]:
        print(f'         {s}')
