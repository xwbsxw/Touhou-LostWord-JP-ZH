# -*- coding: utf-8 -*-
"""导出全部待译界面文字（LocalizeText.jpText 含假名）。

输出：
  lw_work/ui_todo.json  逐条明细（bundle/对象/脚本/层级路径/日文/英文参考）
  lw_work/ui_unique.json 去重后的待译字符串（翻译工作表用）
"""
import os, sys, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work/jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')


def gopath(gos, mgo):
    names = []
    cur = mgo
    for _ in range(14):
        if cur is None:
            break
        d = gos.get(cur)
        if not d:
            break
        names.append(d.get('m_Name', '?'))
        fa = d.get('m_Father')
        cur = fa.get('m_PathID') if isinstance(fa, dict) else None
    return '/'.join(reversed(names))


def main():
    cl = json.load(open(os.path.join(ROOT, 'lw_work/ui_classify.json'), encoding='utf-8'))
    targets = [(r['a'], r['b']) for r in cl if r['ui_n']]

    rows = []
    for a, b in targets:
        p = os.path.join(SRC, a, b, '__data')
        if not os.path.exists(p):
            continue
        try:
            env = UnityPy.load(p)
        except Exception:
            continue
        cls = {}
        gos = {}
        for o in env.objects:
            if o.type.name == 'MonoScript':
                try:
                    cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
                except Exception:
                    pass
            elif o.type.name == 'GameObject':
                try:
                    gos[o.path_id] = o.read_typetree()
                except Exception:
                    pass
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            jp = t.get('jpText')
            if not isinstance(jp, str) or not jp.strip() or not KANA.search(jp):
                continue
            sp = t.get('m_Script') or {}
            cn = cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None
            mgo = t.get('m_GameObject')
            pid = mgo.get('m_PathID') if isinstance(mgo, dict) else None
            rows.append({
                'a': a, 'b': b, 'path_id': o.path_id,
                'script': cn,
                'go': gopath(gos, pid),
                'jpText': jp,
                'enText': t.get('enText'),
                'm_Text': t.get('m_Text'),
                'showingLanguage': t.get('showingLanguage'),
                'isFixedText': t.get('isFixedText'),
            })

    print(f'导出 {len(rows)} 条')

    uniq = collections.OrderedDict()
    for r in rows:
        uniq.setdefault(r['jpText'], []).append(r)
    print(f'去重后 {len(uniq)} 条唯一样本')

    out = []
    for jp, rs in uniq.items():
        out.append({
            'jp': jp,
            'en': rs[0].get('enText'),
            'n': len(rs),
            'where': [f"{r['a'][:8]}:{r['go'][-40:]}" for r in rs[:2]],
        })
    out.sort(key=lambda x: -x['n'])

    json.dump(rows, open(os.path.join(ROOT, 'lw_work/ui_todo.json'), 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(out, open(os.path.join(ROOT, 'lw_work/ui_unique.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)

    lines = [f'共 {len(rows)} 条，去重 {len(out)} 条', '']
    for i, u in enumerate(out):
        lines.append(f"[{i}] x{u['n']}  jp={u['jp']!r}")
        if u['en']:
            lines.append(f"        en={u['en']!r}")
        lines.append(f"        @ {u['where'][0]}")
    open(os.path.join(ROOT, 'lw_work/ui_unique.txt'), 'w',
         encoding='utf-8').write('\n'.join(lines))
    print('明细 -> lw_work/ui_todo.json / ui_unique.txt')


if __name__ == '__main__':
    main()
