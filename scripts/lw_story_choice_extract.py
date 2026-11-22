# -*- coding: utf-8 -*-
"""提取主线剧情包的 SelectOrder 选项文本（m_strfst/m_strsnd/m_str3rd），
去重后导出为翻译工作表。
"""
import os, json, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')

MAIN = [
    ('48696ed27f68c8acd4ae91fcfd1ad6cb', '1d2d470e27aa6bc9e5e2a1b272c7e2c6', 'main0'),
    ('580339df439f3804b452f0120b0854d0', 'f1b3616d93c0177db247fb42ae622dbf', 'main1'),
    ('359f1d36f245cd68b87dbfaf9058ec92', 'b4dfaae3c99fce9525f61ceca3bb1bf9', 'main2'),
]
FIELDS = ('m_strfst', 'm_strsnd', 'm_str3rd')

rows = []
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
        for f in FIELDS:
            v = t.get(f)
            if isinstance(v, str) and v.strip():
                n += 1
                rows.append({'bundle': name, 'a': a, 'b': b,
                             'path_id': o.path_id, 'field': f, 'jp': v})
    print(f'{name}: SelectOrder 选项 {n} 条')

print(f'\n总计 {len(rows)} 条')

uniq = collections.OrderedDict()
for r in rows:
    uniq.setdefault(r['jp'], 0)
    uniq[r['jp']] += 1
print(f'去重后 {len(uniq)} 条')

out = [{'jp': k, 'n': v} for k, v in uniq.items()]
out.sort(key=lambda x: -x['n'])

json.dump(rows, open(os.path.join(ROOT, 'lw_work/choice_todo.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)
json.dump(out, open(os.path.join(ROOT, 'lw_work/choice_unique.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
lines = [f'共 {len(rows)} 条，去重 {len(out)} 条', '']
for i, u in enumerate(out):
    lines.append(f'[{i}] x{u["n"]}  {u["jp"]!r}')
open(os.path.join(ROOT, 'lw_work/choice_unique.txt'), 'w',
     encoding='utf-8').write('\n'.join(lines))
print('-> lw_work/choice_unique.txt')
