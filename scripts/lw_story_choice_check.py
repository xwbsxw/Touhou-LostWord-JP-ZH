# -*- coding: utf-8 -*-
"""检查剧情包 SelectOrder 选项文本的语言，找出英文残留。
同时统计 SelectOrder 有多少条，分布在哪几个包。
"""
import os, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
ASCII = re.compile(r'[A-Za-z]{2,}')

MAIN = [
    ('48696ed27f68c8acd4ae91fcfd1ad6cb', '1d2d470e27aa6bc9e5e2a1b272c7e2c6', 'main0'),
    ('580339df439f3804b452f0120b0854d0', 'f1b3616d93c0177db247fb42ae622dbf', 'main1'),
    ('359f1d36f245cd68b87dbfaf9058ec92', 'b4dfaae3c99fce9525f61ceca3bb1bf9', 'main2'),
]

tot = 0
en_samples = []
for a, b, name in MAIN:
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
        for f in ('m_strfst', 'm_strsnd', 'm_str3rd'):
            v = t.get(f)
            if isinstance(v, str) and v.strip():
                n += 1
                tot += 1
                if ASCII.search(v) and not KANA.search(v) and not HAN.search(v):
                    en_samples.append((name, f, v))
    print(f'{name}: SelectOrder 文本 {n} 条')
print(f'\n总选项文本 {tot} 条')
print(f'纯英文样本 {len(en_samples)} 条')
for s in en_samples[:20]:
    print(f'  {s}')
