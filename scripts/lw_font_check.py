# -*- coding: utf-8 -*-
"""检查日服 TMP 字体资产覆盖了哪些 Unicode 码位，用于判断繁体字会不会缺字形显示成方块。

用法: python lw_font_check.py <bundle_root> <out.json>
"""
import os, sys, json, collections
import UnityPy


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
                keys.append((a, b, f))
    print(f'待扫包 {len(keys)} 个', flush=True)

    covered = set()
    fonts = []
    scanned = 0
    for i, (a, b, f) in enumerate(keys):
        if i % 200 == 0:
            print(f'  {i}/{len(keys)}  字体资产 {len(fonts)}  码位 {len(covered)}', flush=True)
        try:
            env = UnityPy.load(f)
        except Exception:
            continue
        # 预筛：MonoScript 里是否有 TMP_FontAsset
        names = {}
        try:
            for obj in env.objects:
                if obj.type.name == 'MonoScript':
                    names[obj.path_id] = getattr(obj.read(), 'm_ClassName', '') or ''
        except Exception:
            continue
        if 'TMP_FontAsset' not in names.values() and 'FontAsset' not in ''.join(names.values()):
            continue
        want = {p for p, n in names.items() if 'FontAsset' in n}
        if not want:
            continue
        scanned += 1
        for obj in env.objects:
            if obj.type.name != 'MonoBehaviour':
                continue
            try:
                tree = obj.read_typetree()
            except Exception:
                continue
            if not isinstance(tree, dict) or 'm_CharacterTable' not in tree:
                continue
            tbl = tree.get('m_CharacterTable') or []
            cnt = 0
            for e in tbl:
                if isinstance(e, dict):
                    u = e.get('m_Unicode')
                    if isinstance(u, int):
                        covered.add(u)
                        cnt += 1
            fonts.append({'a': a, 'b': b, 'pid': obj.path_id,
                          'name': tree.get('m_Name', ''), 'glyphs': cnt,
                          'atlas': tree.get('m_AtlasPopulationMode')})

    json.dump({'fonts': fonts, 'covered': sorted(covered)},
              open(outp, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'\n字体资产 {len(fonts)} 个（来自 {scanned} 个包），合计覆盖码位 {len(covered)}')
    for f in fonts[:15]:
        print(f"  {f['glyphs']:>6} 字形  {f['name'][:40]}  ({f['a'][:10]})")


if __name__ == '__main__':
    main()
