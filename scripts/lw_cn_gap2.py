# -*- coding: utf-8 -*-
"""针对 out/*.bin 里的日文残留字段，查国服 dump_cn 对应字段的语言，
精确判断可自动化补救的比例。
"""
import os, sys, re, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

CN_DIR = os.path.join(ROOT, 'lw_work', 'dump_cn')
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')

def load_cn(h):
    p = os.path.join(CN_DIR, h + '.msgpack')
    if not os.path.exists(p):
        return None
    try:
        return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None

names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
tot = {'国服有简体(可补救)': 0, '国服也是日文(需手工)': 0, '国服无id(日服新增)': 0, '其他': 0}
samp = {'国服有简体(可补救)': [], '国服也是日文(需手工)': [], '国服无id(日服新增)': []}

for fn in sorted(os.listdir(os.path.join(ROOT, 'out'))):
    if not fn.endswith('.bin'):
        continue
    name = fn[:-4]
    h = names.get(name)
    if not h:
        continue
    cn = load_cn(h)
    obj = msgpack.unpackb(decrypt(open(os.path.join(ROOT, 'out', fn), 'rb').read()),
                          raw=False, strict_map_key=False)
    for k, row in obj.items():
        if not isinstance(row, list):
            continue
        for i, v in enumerate(row):
            if not isinstance(v, str) or not KANA.search(v):
                continue
            if cn is None:
                tot['其他'] += 1
                continue
            c = cn.get(k)
            if not isinstance(c, list) or i >= len(c):
                tot['国服无id(日服新增)'] += 1
                if len(samp['国服无id(日服新增)']) < 5:
                    samp['国服无id(日服新增)'].append((name, k, i, v[:40]))
                continue
            cc = c[i]
            if not isinstance(cc, str) or not cc.strip() or cc == v or KANA.search(cc):
                tot['国服也是日文(需手工)'] += 1
                if len(samp['国服也是日文(需手工)']) < 5:
                    samp['国服也是日文(需手工)'].append((name, k, i, v[:40]))
            elif HAN.search(cc):
                tot['国服有简体(可补救)'] += 1
                if len(samp['国服有简体(可补救)']) < 8:
                    samp['国服有简体(可补救)'].append((name, k, i, v[:30], cc[:30]))

print('=== out 日文残留的国服对应情况 ===')
for k, v in tot.items():
    print(f'  {k:24} {v}')
print()
for label, ss in samp.items():
    print(f'--- {label} 样本 ---')
    for s in ss:
        print('   ', s)
    print()
