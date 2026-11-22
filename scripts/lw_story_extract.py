# -*- coding: utf-8 -*-
"""从 UnityFS 资源包中抽取剧情台词（MessageOrder.m_text）。

用法: python lw_story_extract.py <bundle_root> <out.json> [--limit N]

目录结构约定: <bundle_root>/<A>/<B>/__data

优化: 先只读 MonoScript 的类名做预筛（每包只有几十个 MonoScript，很便宜），
      确认存在 MessageOrder 之后才对该包里对应的 MonoBehaviour 读取 typetree。
"""
import os, sys, json, re, collections
import UnityPy

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
TARGET_CLASSES = {'MessageOrder'}


def scripts_of(env):
    """path_id -> 类名（只读 MonoScript，便宜）"""
    m = {}
    for obj in env.objects:
        if obj.type.name != 'MonoScript':
            continue
        try:
            m[obj.path_id] = getattr(obj.read(), 'm_ClassName', '') or ''
        except Exception:
            pass
    return m


def main():
    root = sys.argv[1]
    outp = sys.argv[2]
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    keys = []
    for a in sorted(os.listdir(root)):
        pa = os.path.join(root, a)
        if not os.path.isdir(pa):
            continue
        for b in os.listdir(pa):
            f = os.path.join(pa, b, '__data')
            if os.path.exists(f):
                keys.append((a, b, f))
    if limit:
        keys = keys[:limit]
    print(f'待扫包 {len(keys)} 个', flush=True)

    rows = []
    hit_bundles = 0
    cls_counter = collections.Counter()

    for i, (a, b, f) in enumerate(keys):
        if i % 100 == 0:
            print(f'  {i}/{len(keys)}  已收台词 {len(rows)}  命中包 {hit_bundles}', flush=True)
        try:
            env = UnityPy.load(f)
        except Exception:
            continue
        smap = scripts_of(env)
        for v in smap.values():
            cls_counter[v] += 1
        want = {pid for pid, n in smap.items() if n in TARGET_CLASSES}
        if not want:
            continue
        hit_bundles += 1
        for obj in env.objects:
            if obj.type.name != 'MonoBehaviour':
                continue
            try:
                tree = obj.read_typetree()
            except Exception:
                continue
            sp = tree.get('m_Script') or {}
            if not isinstance(sp, dict):
                continue
            if sp.get('m_PathID') not in want:
                continue
            txt = tree.get('m_text')
            if not isinstance(txt, str) or not txt.strip():
                continue
            rows.append({
                'a': a, 'b': b, 'pid': obj.path_id,
                'name': tree.get('m_name') or '',
                'attr': tree.get('m_attr') or '',
                'text': txt,
            })

    json.dump(rows, open(outp, 'w', encoding='utf-8'), ensure_ascii=False)
    kana = sum(1 for r in rows if KANA.search(r['text']))
    han = sum(1 for r in rows if HAN.search(r['text']))
    print(f'\n完成: 台词 {len(rows)} 条, 来自 {hit_bundles} 个包')
    print(f'  含假名(日文原样) {kana} 条, 含汉字 {han} 条')
    print(f'  输出 -> {outp}')
    print('\n出现的脚本类名 top 15:')
    for k, v in cls_counter.most_common(15):
        print(f'  {v:>7}  {k}')


if __name__ == '__main__':
    main()
