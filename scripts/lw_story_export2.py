# -*- coding: utf-8 -*-
"""导出剧情全部台词（TalkOrder / MessageOrder 等 m_text），并去重统计。

输出:
  lw_work/story_todo2.json    逐条明细
  lw_work/story_unique2.json  去重后的日文原句（翻译工作表）
  lw_work/story_unique2.txt   可读清单
"""
import os, sys, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work/jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')

STORY_BUNDLES = [
    ('359f1d36f2', None),   # 由下面解析成完整键
]


def main():
    cl = json.load(open(os.path.join(ROOT, 'lw_work/ui_classify.json'), encoding='utf-8'))
    targets = [(r['a'], r['b']) for r in cl if r['story_n']]
    print(f'剧情包 {len(targets)} 个')

    rows = []
    field_names = collections.Counter()
    for a, b in targets:
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
            if not isinstance(t, dict):
                continue
            mt = t.get('m_text')
            if not isinstance(mt, str) or not mt.strip():
                continue
            sp = t.get('m_Script') or {}
            cn = cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None
            field_names[cn] += 1
            rows.append({
                'a': a, 'b': b, 'path_id': o.path_id, 'script': cn,
                'm_name': t.get('m_name'),
                'm_text': mt,
                'kana': bool(KANA.search(mt)),
            })

    print(f'导出台词对象 {len(rows)}')
    print('按脚本类:')
    for k, v in field_names.most_common(8):
        print(f'   {k}: {v}')

    need = [r for r in rows if r['kana']]
    print(f'\n含假名（待译）{len(need)} 条')

    uniq = collections.OrderedDict()
    for r in need:
        uniq.setdefault(r['m_text'], 0)
        uniq[r['m_text']] += 1
    print(f'去重后 {len(uniq)} 条')
    lens = [len(k) for k in uniq]
    print(f'总字符数 {sum(lens)}  平均 {sum(lens)/max(1,len(lens)):.0f}')

    out = [{'jp': k, 'n': v} for k, v in uniq.items()]
    out.sort(key=lambda x: -x['n'])
    json.dump(rows, open(os.path.join(ROOT, 'lw_work/story_todo2.json'), 'w',
                         encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(out, open(os.path.join(ROOT, 'lw_work/story_unique2.json'), 'w',
                        encoding='utf-8'), ensure_ascii=False, indent=1)
    lines = [f'待译 {len(need)} 条，去重 {len(out)} 条', '']
    for i, u in enumerate(out):
        lines.append(f'[{i}] x{u["n"]} {u["jp"]!r}')
    open(os.path.join(ROOT, 'lw_work/story_unique2.txt'), 'w',
         encoding='utf-8').write('\n'.join(lines))
    print('-> lw_work/story_unique2.txt')


if __name__ == '__main__':
    main()
