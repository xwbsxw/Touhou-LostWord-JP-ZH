# -*- coding: utf-8 -*-
"""定位剧情台词组件 MessageOrder 的字段结构，并抽取真实台词样本。"""
import os, sys, json, re, collections
ROOT = os.path.dirname(os.path.abspath(__file__))
BDIR = os.path.join(ROOT, 'dl', 'ext', 'lwlocal', 'bundles')
import UnityPy

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')

TARGET = '3f4e96d95e97ecc71b95e425c30d3785'
p = os.path.join(BDIR, TARGET)
sub = os.listdir(p)[0]
fp = os.path.join(p, sub, '__data')
print('bundle:', TARGET, os.path.getsize(fp), 'bytes')

env = UnityPy.load(fp)
keys = collections.Counter()
samples = []
kana_samples = []

for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    try:
        d = obj.read()
        sc = getattr(d, 'm_Script', None)
        cls = sc.read().m_ClassName if sc else '?'
    except Exception:
        continue
    if cls != 'MessageOrder':
        continue
    try:
        tree = obj.read_typetree()
    except Exception:
        continue
    for k in tree.keys():
        keys[k] += 1
    # 找长文本字段
    for k, v in tree.items():
        if isinstance(v, str) and len(v) >= 6 and (HAN.search(v) or KANA.search(v)):
            if KANA.search(v):
                if len(kana_samples) < 6:
                    kana_samples.append((k, v))
            elif len(samples) < 10:
                samples.append((k, v))

print('\nMessageOrder 字段出现次数:')
for k, v in keys.most_common(20):
    print(f'  {v:>6}  {k}')

print('\n=== 中文台词样本 ===')
for k, v in samples:
    print(f'  [{k}] {v[:70]}')
print('\n=== 仍含假名的字段样本 ===')
for k, v in kana_samples:
    print(f'  [{k}] {v[:70]}')
