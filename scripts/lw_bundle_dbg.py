# -*- coding: utf-8 -*-
"""调试单个 bundle：确认 UnityPy 1.25.4 下的对象类型统计与 typetree 正确读法。"""
import os, sys, traceback
ROOT = os.path.dirname(os.path.abspath(__file__))
BDIR = os.path.join(ROOT, 'dl', 'ext', 'lwlocal', 'bundles')

import UnityPy

# 取第一个有 __data 的包
p = None
for a in sorted(os.listdir(BDIR)):
    pa = os.path.join(BDIR, a)
    if os.path.isdir(pa):
        for b in os.listdir(pa):
            f = os.path.join(pa, b, '__data')
            if os.path.exists(f):
                p = f
                break
    if p:
        break
print('sample bundle:', p, os.path.getsize(p), 'bytes')

env = UnityPy.load(p)
types = {}
for obj in env.objects:
    types[obj.type.name] = types.get(obj.type.name, 0) + 1
print('\nobject types:', types)

# 找第一个 MonoBehaviour 试各种读法
for obj in env.objects:
    if obj.type.name != 'MonoBehaviour':
        continue
    print('\n--- MonoBehaviour path_id', obj.path_id, '---')
    try:
        d = obj.read()
        print('read() ok:', type(d).__name__)
        print('  attrs sample:', [a for a in dir(d) if not a.startswith('_')][:15])
    except Exception:
        print('read() FAILED'); traceback.print_exc()
        continue
    for how in ('obj.read_typetree', 'd.read_typetree'):
        try:
            if how == 'obj.read_typetree':
                tree = obj.read_typetree()
            else:
                tree = d.read_typetree()
            ks = list(tree.keys())[:20] if isinstance(tree, dict) else None
            print(f'  {how} OK, keys={ks}')
            break
        except Exception as e:
            print(f'  {how} failed: {type(e).__name__}: {e}')
    try:
        sc = getattr(d, 'm_Script', None)
        if sc:
            s = sc.read()
            print('  m_Script class:', getattr(s, 'm_ClassName', '?'))
    except Exception as e:
        print('  m_Script err:', e)
    break
