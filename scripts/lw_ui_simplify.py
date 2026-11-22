# -*- coding: utf-8 -*-
"""对 UI 包（ui_out + ui_text_out）做繁改简：所有 MonoBehaviour 字符串字段 t2s，
排除含假名的日文残留。就地写回。
"""
import os, sys, re
import UnityPy
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
T2S = OpenCC('t2s')
KANA = re.compile(r'[\u3040-\u30ff]')
CJK = re.compile(r'[\u4e00-\u9fff]')
SKIP_FIELDS = {'m_GameObject', 'm_Script'}

def simplify(v):
    if not isinstance(v, str) or not v.strip():
        return v
    if KANA.search(v):
        return v
    if not CJK.search(v):
        return v
    s = T2S.convert(v)
    return s if s != v else v

for d in ('ui_out', 'ui_text_out'):
    p = os.path.join(ROOT, 'lw_work', d)
    if not os.path.isdir(p):
        continue
    total_changed = 0
    for fn in sorted(os.listdir(p)):
        if not fn.endswith('__data'):
            continue
        fp = os.path.join(p, fn)
        env = UnityPy.load(fp)
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
            changed = False
            for k, v in t.items():
                if k in SKIP_FIELDS:
                    continue
                if isinstance(v, str):
                    s = simplify(v)
                    if s != v:
                        t[k] = s
                        changed = True
            if changed:
                o.save_typetree(t)
                n += 1
        if n:
            raw = env.file.save(packer='original')
            open(fp, 'wb').write(raw)
            total_changed += n
    print(f'{d}: 修改 {total_changed} 个对象')
