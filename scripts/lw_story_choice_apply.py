# -*- coding: utf-8 -*-
"""把剧情选项（SelectOrder）译文写回主线 3 个包。

- 键 = 日文原文（含真实 \\x1bh）
- 值里的 {P} 还原成 \\x1bh
- 基底用 story_sc_out 里已推的中文版（保留 m_text 译文）
"""
import os, sys, json, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_story_choice_sc import CHOICE_SC_1

SRC = os.path.join(ROOT, 'lw_work', 'story_sc_out')   # 已推中文版基底
OUT = os.path.join(ROOT, 'lw_work', 'story_sc_out')

MAIN = [
    ('48696ed27f68c8acd4ae91fcfd1ad6cb', '1d2d470e27aa6bc9e5e2a1b272c7e2c6'),
    ('580339df439f3804b452f0120b0854d0', 'f1b3616d93c0177db247fb42ae622dbf'),
    ('359f1d36f245cd68b87dbfaf9058ec92', 'b4dfaae3c99fce9525f61ceca3bb1bf9'),
]
FIELDS = ('m_strfst', 'm_strsnd', 'm_str3rd')

write = '--write' in sys.argv

# 先检查覆盖
todo = json.load(open(os.path.join(ROOT, 'lw_work/choice_todo.json'), encoding='utf-8'))
miss = set()
for r in todo:
    if r['jp'] not in CHOICE_SC_1:
        miss.add(r['jp'])
print(f'选项 {len(todo)} 条，未覆盖 {len(miss)} 种')
for m in list(miss)[:20]:
    print(f'  ! {m!r}')

if miss:
    print('  有未覆盖，中止（请补译）')
    sys.exit(1)

if not write:
    print('（未写入，加 --write）')
    sys.exit()

total = 0
for a, b in MAIN:
    p = os.path.join(SRC, f'{a}__{b}__data')
    if not os.path.exists(p):
        print(f'  跳过（无基底）{a[:8]}')
        continue
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
        changed = False
        for f in FIELDS:
            v = t.get(f)
            if isinstance(v, str) and v.strip() and v in CHOICE_SC_1:
                t[f] = CHOICE_SC_1[v].replace('{P}', '\x1bh')
                changed = True
                n += 1
        if changed:
            o.save_typetree(t)
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    total += n
    print(f'  {a[:10]}…  写回选项 {n} 条  -> {len(raw)} B')

print(f'\n共写回 {total} 条选项')
