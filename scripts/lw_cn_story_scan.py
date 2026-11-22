# -*- coding: utf-8 -*-
"""扫描国服缓存，找出含剧情组件（TalkOrder/MessageOrder）的包，统计中文/日文比例。

用法: python lw_cn_story_scan.py <root> <out.json>
"""
import os, sys, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
STORY = {'TalkOrder', 'MessageOrder'}


def main():
    root = sys.argv[1]
    outp = sys.argv[2]
    keys = []
    for a in sorted(os.listdir(root)):
        pa = os.path.join(root, a)
        if not os.path.isdir(pa):
            continue
        for b in os.listdir(pa):
            f = os.path.join(pa, b, '__data')
            if os.path.exists(f):
                keys.append((a, b, f, os.path.getsize(f)))
    print(f'待扫 {len(keys)} 包', flush=True)

    out = []
    for i, (a, b, f, sz) in enumerate(keys):
        if i % 400 == 0:
            print(f'  {i}/{len(keys)}  命中 {len(out)}', flush=True)
        try:
            env = UnityPy.load(f)
        except Exception:
            continue
        cls = {}
        for o in env.objects:
            if o.type.name == 'MonoScript':
                try:
                    cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
                except Exception:
                    pass
        if not (STORY & set(cls.values())):
            continue
        cn_n = ja_n = other = 0
        order = []
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
            c = cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None
            if c in STORY:
                order.append((o.path_id, mt))
            if KANA.search(mt):
                ja_n += 1
            elif HAN.search(mt):
                cn_n += 1
            else:
                other += 1
        if not order:
            continue
        out.append({'a': a, 'b': b, 'size': sz, 'cn': cn_n, 'ja': ja_n,
                    'other': other, 'n': len(order)})

    out.sort(key=lambda x: -x['cn'])
    json.dump(out, open(outp, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n含剧情组件包 {len(out)} 个')
    print('中文台词最多的前 15:')
    for r in out[:15]:
        print(f"  {r['a'][:10]}/{r['b'][:8]}  台词{r['n']:>5} 中文{r['cn']:>5} "
              f"日文{r['ja']:>5}  {r['size']} B")
    tot_cn = sum(r['cn'] for r in out)
    tot_ja = sum(r['ja'] for r in out)
    print(f'\n合计中文 {tot_cn} 条，日文 {tot_ja} 条')


if __name__ == '__main__':
    main()
