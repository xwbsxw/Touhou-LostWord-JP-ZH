# -*- coding: utf-8 -*-
"""扫描全部剧情包的 SelectOrder 选项语言分布，定位英文来源。"""
import os, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
ASCII = re.compile(r'[A-Za-z]{2,}')

cl = json.load(open(os.path.join(ROOT, 'lw_work/ui_classify.json'), encoding='utf-8'))
story = [(r['a'], r['b']) for r in cl if r['story_n']]
print(f'剧情包 {len(story)} 个')

for a, b in story:
    p = os.path.join(SRC, a, b, '__data')
    if not os.path.exists(p):
        continue
    env = UnityPy.load(p)
    cls = {}
    for o in env.objects:
        if o.type.name == 'MonoScript':
            try:
                cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
            except Exception:
                pass
    rows = []
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
        for f in ('m_strfst', 'm_strsnd', 'm_str3rd'):
            v = t.get(f)
            if isinstance(v, str) and v.strip():
                lang = 'EN' if (ASCII.search(v) and not KANA.search(v) and not HAN.search(v)) else ('JA' if KANA.search(v) else '??')
                rows.append((f, lang, v))
    en = [r for r in rows if r[1] == 'EN']
    print(f'{a[:10]}/{b[:8]}: SelectOrder {len(rows)} 条，英文 {len(en)}')
    for f, lang, v in en[:6]:
        print(f'    [{f}] {v!r}')
