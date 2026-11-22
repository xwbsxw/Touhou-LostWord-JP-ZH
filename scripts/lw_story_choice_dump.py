# -*- coding: utf-8 -*-
"""dump SelectOrder 完整 typetree，看是否引用英文资源或有多语言字段。"""
import os, json
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')

a, b = '359f1d36f245cd68b87dbfaf9058ec92', 'b4dfaae3c99fce9525f61ceca3bb1bf9'
p = os.path.join(SRC, a, b, '__data')
env = UnityPy.load(p)
cls = {}
for o in env.objects:
    if o.type.name == 'MonoScript':
        try:
            cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
        except Exception:
            pass

n = 0
for o in env.objects:
    if o.type.name != 'MonoBehaviour':
        continue
    try:
        t = o.read_typetree()
    except Exception:
        continue
    if not isinstance(t, dict):
        continue
    sp = t.get('m_Script') or {}
    cn = cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None
    if cn != 'SelectOrder':
        continue
    print(f'=== SelectOrder path_id={o.path_id} ===')
    for k, v in sorted(t.items()):
        s = repr(v)
        if len(s) > 120:
            s = s[:120] + '...'
        print(f'  {k}: {s}')
    n += 1
    if n >= 3:
        break
