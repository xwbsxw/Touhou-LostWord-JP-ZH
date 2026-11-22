# -*- coding: utf-8 -*-
"""导出普通 Text 组件的 m_Text（含假名、且对象没有 jpText 字段）。"""
import os, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work/jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')


def main():
    cl = json.load(open(os.path.join(ROOT, 'lw_work/ui_classify.json'), encoding='utf-8'))
    rows = []
    for r in cl:
        a, b = r['a'], r['b']
        p = os.path.join(SRC, a, b, '__data')
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
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict) or 'jpText' in t:
                continue
            mt = t.get('m_Text')
            if not isinstance(mt, str) or not mt.strip() or not KANA.search(mt):
                continue
            sp = t.get('m_Script') or {}
            rows.append({
                'a': a, 'b': b, 'path_id': o.path_id,
                'script': cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None,
                'm_Text': mt,
            })

    print(f'导出 {len(rows)} 条')
    uniq = collections.OrderedDict()
    for r in rows:
        uniq.setdefault(r['m_Text'], 0)
        uniq[r['m_Text']] += 1
    out = [{'jp': k, 'n': v} for k, v in uniq.items()]
    out.sort(key=lambda x: -x['n'])
    print(f'去重 {len(out)} 条')

    json.dump(rows, open(os.path.join(ROOT, 'lw_work/ui_text_todo.json'), 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(out, open(os.path.join(ROOT, 'lw_work/ui_text_unique.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = [f'共 {len(rows)} 条，去重 {len(out)} 条', '']
    for i, u in enumerate(out):
        lines.append(f'[{i}] x{u["n"]}  {u["jp"]!r}')
    open(os.path.join(ROOT, 'lw_work/ui_text_unique.txt'), 'w',
         encoding='utf-8').write('\n'.join(lines))
    print('-> lw_work/ui_text_unique.txt')


if __name__ == '__main__':
    main()
