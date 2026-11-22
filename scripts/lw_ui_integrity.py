# -*- coding: utf-8 -*-
"""对比 UI 包：原始 jpuc3 vs 我重新保存的 ui_out/ui_text_out，
检查对象数、MonoBehaviour 数、可读性、以及被改动字段是否属于"数据字段"（JSON/路径/ID）。
"""
import os, sys, re, json
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')

# 看起来像"数据"而非"显示文本"的特征
DATA_PAT = re.compile(r'^\s*[\[{]')          # JSON
PATH_PAT = re.compile(r'^[\w/.\-]+\.(png|prefab|ogg|mat|asset|json|txt)$', re.I)
ID_PAT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')   # 纯标识符

def summarize(path):
    try:
        env = UnityPy.load(path)
    except Exception as e:
        return None, f'加载失败 {e}'
    n_obj = 0
    n_mb = 0
    n_err = 0
    for o in env.objects:
        n_obj += 1
        if o.type.name == 'MonoBehaviour':
            n_mb += 1
            try:
                t = o.read_typetree()
                if not isinstance(t, dict):
                    n_err += 1
            except Exception:
                n_err += 1
    return (n_obj, n_mb, n_err), None

for d in ('ui_out', 'ui_text_out'):
    p = os.path.join(ROOT, 'lw_work', d)
    if not os.path.isdir(p):
        continue
    print(f'===== {d} =====')
    bad = []
    for fn in sorted(os.listdir(p)):
        if not fn.endswith('__data'):
            continue
        a, b, _ = fn.split('__')
        orig = os.path.join(SRC, a, b, '__data')
        if not os.path.exists(orig):
            continue
        so, eo = summarize(orig)
        sn, en = summarize(os.path.join(p, fn))
        if eo or en:
            bad.append((fn[:10], 'orig:' + str(eo), 'new:' + str(en)))
            continue
        if so[0] != sn[0] or so[1] != sn[1]:
            bad.append((fn[:10], f'obj {so[0]}->{sn[0]}', f'mb {so[1]}->{sn[1]}'))
        if sn[2]:
            bad.append((fn[:10], f'读取失败 {sn[2]}'))
    print(f'  异常包 {len(bad)}')
    for x in bad[:12]:
        print('    ', x)
    print()
