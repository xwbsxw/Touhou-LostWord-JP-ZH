# -*- coding: utf-8 -*-
"""检查 out/ 里所有表的 string.Format 占位符完整性（对比日文原版 dumped/）。

若译文里的占位符 {n} / {n:...} 与原版不一致，会导致游戏 string.Format 异常，
进而界面卡死/黑屏。
"""
import os, json, re, msgpack, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt

ROOT = os.path.dirname(os.path.abspath(__file__))
names = json.load(open(os.path.join(ROOT, 'lw_work/table_names.json'), encoding='utf-8'))
PH = re.compile(r'\{(\d+)(?::[^{}]*)?\}')

def load(path, encrypted=True):
    raw = open(path, 'rb').read()
    try:
        if encrypted:
            return msgpack.unpackb(decrypt(raw), raw=False, strict_map_key=False)
        return msgpack.unpackb(raw, raw=False, strict_map_key=False)
    except Exception:
        return None

def ph_set(s):
    return set(PH.findall(s))

bad = []
checked = 0
for name in sorted(os.listdir(os.path.join(ROOT, 'out'))):
    if not name.endswith('.bin'):
        continue
    tn = name[:-4]
    h = names.get(tn)
    if not h:
        continue
    jp_path = os.path.join(ROOT, 'dumped', h + '.msgpack')
    out_path = os.path.join(ROOT, 'out', name)
    if not os.path.exists(jp_path):
        continue
    jp = load(jp_path, encrypted=False)   # dumped 是已解密的裸 msgpack
    ou = load(out_path, encrypted=True)
    if jp is None or ou is None:
        print(f'!! {tn}: 解析失败 jp={jp is not None} out={ou is not None}')
        continue
    for rid in jp:
        if rid not in ou:
            continue
        jrow = jp[rid]
        orow = ou[rid]
        if not isinstance(jrow, list) or not isinstance(orow, list):
            continue
        for i in range(min(len(jrow), len(orow))):
            jv = jrow[i]
            ov = orow[i]
            if not isinstance(jv, str) or not isinstance(ov, str):
                continue
            pj = ph_set(jv)
            po = ph_set(ov)
            if pj != po:
                bad.append((tn, rid, i, pj, po, jv[:40], ov[:40]))
    checked += 1

print(f'检查 {checked} 张表，占位符不一致 {len(bad)} 处')
for tn, rid, i, pj, po, jv, ov in bad[:30]:
    print(f'  [{tn} id={rid} f={i}] 原{pj} 译{po}')
    print(f'     日: {jv}')
    print(f'     中: {ov}')
