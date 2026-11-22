# -*- coding: utf-8 -*-
"""对比签到相关表：日文原版 dumped/ vs 当前 out/，找出异常改动
（空字符串、行丢失、格式串变化、占位符变化）。
"""
import os, sys, re, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

PH = re.compile(r'\{(\d+)(?::[^{}]*)?\}')
TAG = re.compile(r'</?([A-Za-z]+)')

TABLES = ['Loginbonus', 'LoginbonusReward', 'RandomLoginBonus', 'SlotLoginBonus',
          'SlotLoginBonusResult', 'EventLoginbonus', 'Item', 'CommonString']

def load_jp(name):
    names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
    h = names.get(name)
    if not h:
        return None
    p = os.path.join(ROOT, 'dumped', h + '.msgpack')
    if not os.path.exists(p):
        return None
    return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)

def load_out(name):
    p = os.path.join(ROOT, 'out', name + '.bin')
    if not os.path.exists(p):
        return None
    return msgpack.unpackb(decrypt(open(p, 'rb').read()), raw=False, strict_map_key=False)

for tn in TABLES:
    jp = load_jp(tn)
    ou = load_out(tn)
    print(f'===== {tn} =====')
    if jp is None:
        print('  日文原版缺失')
        continue
    if ou is None:
        print(f'  未生成 out/（保持日文原样）  JP 行数 {len(jp)}')
        continue
    print(f'  JP 行 {len(jp)} / OUT 行 {len(ou)}')
    # 行集合差异
    miss = set(jp) - set(ou)
    if miss:
        print(f'  !! OUT 缺行 {len(miss)}: {list(miss)[:5]}')
    # 字段级检查
    empty = []
    ph_bad = []
    tag_bad = []
    changed = 0
    for k, jv in jp.items():
        ov = ou.get(k)
        if not isinstance(jv, list) or not isinstance(ov, list):
            continue
        for i in range(min(len(jv), len(ov))):
            j = jv[i]
            o = ov[i]
            if not isinstance(j, str):
                continue
            if j == o:
                continue
            changed += 1
            if not isinstance(o, str) or not o.strip():
                empty.append((k, i, j[:30], repr(o)[:20]))
                continue
            if sorted(PH.findall(j)) != sorted(PH.findall(o)):
                ph_bad.append((k, i, sorted(PH.findall(j)), sorted(PH.findall(o)), j[:30], o[:30]))
            if sorted(TAG.findall(j)) != sorted(TAG.findall(o)):
                tag_bad.append((k, i, j[:30], o[:30]))
    print(f'  改动字段 {changed}')
    if empty:
        print(f'  !! 空/空白字符串 {len(empty)}:')
        for x in empty[:8]:
            print('      ', x)
    if ph_bad:
        print(f'  !! 占位符不一致 {len(ph_bad)}:')
        for x in ph_bad[:8]:
            print('      ', x)
    if tag_bad:
        print(f'  !! 标签不一致 {len(tag_bad)}:')
        for x in tag_bad[:5]:
            print('      ', x)
    print()
