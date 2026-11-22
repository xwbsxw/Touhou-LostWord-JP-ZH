# -*- coding: utf-8 -*-
"""定量检测：设备 master 表里还有多少「简体专有字」。
只要命中就是没转繁的漏网，按表统计。
"""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt
import msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(ROOT, 'lw_work', 'jpcache', 'jpcache')
names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
H2N = {v: k for k, v in names.items()}

# 只在简体里出现、繁体不会用的字
SC_ONLY = set('狱无离谱猫帮这说时会后们对开关门问间见现点电东车马鸟鱼龙龟'
              '书笔买卖读语请谢让认识该谁吗呢吧啊哟'
              '国图团园围国过还进运达远边连选适'
              '华协单卖厂历压厌厅县参双发变义'
              '从众优会伟传伤价众体余佛作侧们'
              '儿党兰关兴养兽内冈冲决况准减凤'
              '刘则刚创删别刹刬剌前剑剧劝办务动励'
              '劳势勋勐勚匀匦匮区医华协单卖')
SC_ONLY = {c for c in SC_ONLY if c.strip()}

per = collections.Counter()
samples = collections.defaultdict(list)

for p in os.listdir(CACHE):
    fp = os.path.join(CACHE, p)
    try:
        obj = msgpack.unpackb(decrypt(open(fp, 'rb').read()), raw=False, strict_map_key=False)
    except Exception:
        continue
    if not isinstance(obj, dict):
        continue
    tn = H2N.get(p, p[:8])
    for rid, row in obj.items():
        if not isinstance(row, (list, tuple)):
            continue
        for i, v in enumerate(row):
            if not isinstance(v, str):
                continue
            hit = SC_ONLY & set(v)
            if hit:
                per[tn] += 1
                if len(samples[tn]) < 3:
                    samples[tn].append(f'[{i}]id={rid}: {v[:46]}')

print(f'含简体字的表 {len(per)} 张，字段合计 {sum(per.values())}')
print()
for tn, n in per.most_common(20):
    print(f'{n:>6}  {tn}')
    for s in samples[tn]:
        print(f'          {s}')
