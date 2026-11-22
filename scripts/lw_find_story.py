# -*- coding: utf-8 -*-
"""扫描日服全部主表，找出「长日文句子」密集的表 —— 用来判断剧情台词是否其实在主表里。"""
import os, sys, json, re, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
DUMP = os.path.join(ROOT, 'dumped')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
H2N = {v: k for k, v in names.items()}
KANA = re.compile(r'[\u3040-\u30ff]')

long_cnt = collections.Counter()
sent_cnt = collections.Counter()
samples = collections.defaultdict(list)
files = 0

for fn in os.listdir(DUMP):
    if not fn.endswith('.msgpack'):
        continue
    h = fn[:-8]
    try:
        raw = open(os.path.join(DUMP, fn), 'rb').read()
        try:
            obj = msgpack.unpackb(raw, raw=False, strict_map_key=False)
        except Exception:
            obj = msgpack.unpackb(decrypt(raw), raw=False, strict_map_key=False)
    except Exception:
        continue
    files += 1
    if not isinstance(obj, dict):
        continue
    tn = H2N.get(h, h[:8])
    for rid, row in obj.items():
        if not isinstance(row, (list, tuple)):
            continue
        for i, v in enumerate(row):
            if not isinstance(v, str) or len(v) < 12:
                continue
            if not KANA.search(v):
                continue
            long_cnt[tn] += 1
            # 句子特征：含句号/问号/感叹号，且不只一个分句
            if v.count('。') + v.count('！') + v.count('？') >= 1 and len(v) >= 20:
                sent_cnt[tn] += 1
                if len(samples[tn]) < 3:
                    samples[tn].append(f'[{i}]id={rid}: {v[:70]}')

print(f'扫描主表 {files} 张 / 名称表 {len(names)} 条')
print(f'\n=== 含「日文长句」最多的表 top 15 ===')
for tn, n in sent_cnt.most_common(15):
    print(f'{n:>6}  {tn}   (长日文串总计 {long_cnt[tn]})')
    for s in samples[tn]:
        print(f'          {s}')

print(f'\n=== 全部含长日文串的表 ===')
for tn, n in long_cnt.most_common(40):
    print(f'{n:>6}  {tn}')
