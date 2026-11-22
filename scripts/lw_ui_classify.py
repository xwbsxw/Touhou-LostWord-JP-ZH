# -*- coding: utf-8 -*-
"""把 96 个含文本的包分成「剧情包」和「界面包」，给出各自的真实待译量。"""
import os, sys, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work/jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')
census = json.load(open(os.path.join(ROOT, 'lw_work/ui_census.json'), encoding='utf-8'))

rows = []
for r in census:
    p = os.path.join(SRC, r['a'], r['b'], '__data')
    if not os.path.exists(p):
        continue
    try:
        env = UnityPy.load(p)
    except Exception:
        continue
    cls = {}
    for o in env.objects:
        if o.type.name == 'MonoScript':
            try:
                cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
            except Exception:
                pass
    story = collections.Counter()
    ui = collections.Counter()
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
        mt = t.get('m_text')
        if isinstance(mt, str) and mt.strip() and KANA.search(mt):
            story[cn] += 1
        jp = t.get('jpText')
        if isinstance(jp, str) and jp.strip() and KANA.search(jp):
            ui[cn] += 1
    rows.append({
        'a': r['a'], 'b': r['b'], 'size': r['size'],
        'story': dict(story), 'ui': dict(ui),
        'story_n': sum(story.values()), 'ui_n': sum(ui.values()),
    })

story_b = [r for r in rows if r['story_n']]
ui_b = [r for r in rows if r['ui_n']]
print(f'剧情包（含 m_text 待译）{len(story_b)} 个，合计 {sum(r["story_n"] for r in story_b)} 条')
for r in sorted(story_b, key=lambda x: -x['story_n']):
    cls = ', '.join(f'{k}:{v}' for k, v in
                    sorted(r['story'].items(), key=lambda x: -x[1])[:3])
    print(f"  {r['a'][:10]}  {r['story_n']:>5} 条  [{cls}]")

print(f'\n界面包（含 jpText 待译）{len(ui_b)} 个，合计 {sum(r["ui_n"] for r in ui_b)} 条')
tot_ui = collections.Counter()
for r in ui_b:
    tot_ui.update(r['ui'])
print('  涉及的脚本类:', dict(tot_ui.most_common(6)))

json.dump(rows, open(os.path.join(ROOT, 'lw_work/ui_classify.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n明细 -> lw_work/ui_classify.json')
