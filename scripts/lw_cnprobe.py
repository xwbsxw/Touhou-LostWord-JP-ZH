# -*- coding: utf-8 -*-
"""探测：国际服汉化包 (lwlocal v1.4) 的 70 张主表能否用日服同一套 key/IV 解出。"""
import os, sys, json, glob, hashlib
import msgpack
sys.path.insert(0, '.')
from lw_master import decrypt

SRC = 'dl/ext/lwlocal/master'
DST = 'dl/ext/lwlocal/dec'
os.makedirs(DST, exist_ok=True)

names = json.load(open('lw_work/table_names.json', encoding='utf-8'))
rev = {v: k for k, v in names.items()}

ok, bad, unknown = [], [], []
for f in sorted(glob.glob(os.path.join(SRC, '*'))):
    h = os.path.basename(f)
    raw = open(f, 'rb').read()
    try:
        pt = decrypt(raw)
        o = msgpack.unpackb(pt, raw=False, strict_map_key=False)
    except Exception as e:
        bad.append((h, repr(e)[:60]))
        continue
    open(os.path.join(DST, h + '.msgpack'), 'wb').write(pt)
    nm = rev.get(h)
    if nm is None:
        unknown.append((h, len(o)))
    ok.append((nm or '?', h, len(o)))

print(f'解密成功 {len(ok)} / 失败 {len(bad)}')
print(f'名字已知 {sum(1 for n,_,_ in ok if n!="?")} / 未知 {len(unknown)}')
if bad:
    print('--- 失败 ---')
    for h, e in bad[:10]:
        print(' ', h, e)
if unknown:
    print('--- 未知 hash（前 30）---')
    for h, n in unknown[:30]:
        print(' ', h, n)
print('--- 成功清单（前 20）---')
for n, h, c in ok[:20]:
    print(f'  {n:28s} rows={c:<6} {h}')
