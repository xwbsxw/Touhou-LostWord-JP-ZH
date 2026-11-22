# -*- coding: utf-8 -*-
"""检查日文残留字段在国服 dump_cn 里的对应情况：
- 国服是简体中文（可自动对齐，但被闸门拒绝）→ 可补救
- 国服也是日文（国服没翻译）→ 需手工
- 国服无该 id（日服新增）→ 需手工
"""
import os, sys, re, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

JP_DIR = os.path.join(ROOT, 'dumped')
CN_DIR = os.path.join(ROOT, 'lw_work', 'dump_cn')
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')

def load(p):
    try:
        return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None

tot = {'cn_has_cn': 0, 'cn_is_ja': 0, 'cn_missing_id': 0, 'cn_missing_field': 0, 'other': 0}
samples = {'cn_has_cn': [], 'cn_is_ja': [], 'cn_missing_id': []}

for name, h in sorted(NAMES.items()):
    jp = load(os.path.join(JP_DIR, h + '.msgpack'))
    cn = load(os.path.join(CN_DIR, h + '.msgpack'))
    if jp is None or cn is None:
        continue
    for k, jv in jp.items():
        if not isinstance(jv, list):
            continue
        cv = cn.get(k)
        for i, x in enumerate(jv):
            if not isinstance(x, str) or not KANA.search(x):
                continue  # 只看日文残留（含假名）
            if cv is None or not isinstance(cv, list):
                tot['cn_missing_id'] += 1
                if len(samples['cn_missing_id']) < 3:
                    samples['cn_missing_id'].append((name, k, i, x[:40]))
                continue
            if i >= len(cv):
                tot['cn_missing_field'] += 1
                continue
            c = cv[i]
            if not isinstance(c, str) or not c.strip() or c == x:
                tot['cn_is_ja'] += 1
                if len(samples['cn_is_ja']) < 3:
                    samples['cn_is_ja'].append((name, k, i, x[:40]))
            elif HAN.search(c) and not KANA.search(c):
                tot['cn_has_cn'] += 1
                if len(samples['cn_has_cn']) < 3:
                    samples['cn_has_cn'].append((name, k, i, x[:30], c[:30]))
            else:
                tot['other'] += 1

print('=== 日文残留字段的国服对应情况 ===')
for k, v in tot.items():
    print(f'  {k:18} {v}')
print('\n国服有简体译文（可补救）样本:')
for s in samples['cn_has_cn']:
    print('   ', s)
print('\n国服也是日文（需手工）样本:')
for s in samples['cn_is_ja']:
    print('   ', s)
print('\n国服无该 id（日服新增）样本:')
for s in samples['cn_missing_id']:
    print('   ', s)
