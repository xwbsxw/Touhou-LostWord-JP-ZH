# -*- coding: utf-8 -*-
"""剧情回写：按行序索引把简体译文写入 m_text。

用法:
  python lw_story_apply.py <翻译模块名> [--write]
例如:
  python lw_story_apply.py lw_story_sc_36da --write

翻译模块需提供 BUNDLE（"A/B"）与 SC（{索引: 译文}）。
译文里的 {P} 会还原成 \\x1bh（玩家名占位符）。
"""
import os, sys, json, importlib
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work/jpuc3')
OUT = os.path.join(ROOT, 'lw_work/story_sc_out')

PLACEHOLDER = '{P}'
REAL = '\x1bh'
ESCMARK = '{E}'
ESCREAL = '\x1b'


def restore(s):
    """把 {P} 还原成玩家名占位符、{E} 还原成 ESC 控制码前缀。"""
    return s.replace(PLACEHOLDER, REAL).replace(ESCMARK, ESCREAL)


def main():
    mod_name = sys.argv[1]
    write = '--write' in sys.argv
    mod = importlib.import_module(mod_name)
    a, b = mod.BUNDLE.split('/')
    tr = mod.SC

    rows = [r for r in json.load(open(os.path.join(ROOT, 'lw_work/story_todo2.json'),
                                      encoding='utf-8'))
            if r['a'] == a and r['b'] == b]
    need = [i for i, r in enumerate(rows) if r['kana']]

    # 序号模式：SC 的键是 1..N（只数待译行），按顺序绑定到对象，
    # 避免手工追踪原始行号造成的漂移。
    if getattr(mod, 'ORDINAL', False):
        n_need = len(need)
        print(f'{a[:10]}…  待译 {n_need} 行（序号模式），译文 {len(tr)} 条')
        missing = [o for o in range(1, n_need + 1) if o not in tr]
        extra = [o for o in tr if o < 1 or o > n_need]
        partial = getattr(mod, 'ALLOW_PARTIAL', False)
        if missing:
            tag = '缺' if not partial else '未译'
            print(f'  {tag} {len(missing)} 条（已译 {len(tr)}/{n_need}'
                  f'，{len(tr)/n_need*100:.0f}%）')
        if extra:
            print(f'  !! 越界序号 {extra[:20]}')
            print('  已中止')
            return
        if missing and not partial:
            print('  已中止（请补齐，或设 ALLOW_PARTIAL=True 分批写入）')
            return
        want = {}
        for o, sc in tr.items():
            want[rows[need[o - 1]]['path_id']] = restore(sc)
        print(f'  写回 {len(want)} 个对象')
        if not write:
            print('  （未写入，加 --write）')
            return
        # 基底优先用已有产物（含前几批译文），否则用原始日文包
        p = os.path.join(OUT, f'{a}__{b}__data')
        if not os.path.exists(p):
            p = os.path.join(SRC, a, b, '__data')
        env = UnityPy.load(p)
        n = 0
        for ob in env.objects:
            if ob.type.name != 'MonoBehaviour':
                continue
            sc = want.get(ob.path_id)
            if sc is None:
                continue
            t = ob.read_typetree()
            t['m_text'] = sc
            ob.save_typetree(t)
            n += 1
        os.makedirs(OUT, exist_ok=True)
        dst = os.path.join(OUT, f'{a}__{b}__data')
        raw = env.file.save(packer='original')
        open(dst, 'wb').write(raw)
        print(f'  实际写回 {n}，输出 {dst}  {os.path.getsize(p)} -> {len(raw)} B')
        return

    print(f'{a[:10]}…  该包台词 {len(rows)} 条（含假名 {len(need)} 条），译文 {len(tr)} 条')
    missing = [i for i in need if i not in tr]
    extra = [i for i in tr if i >= len(rows)]
    if missing:
        print(f'  !! 缺少索引 {missing[:20]}（共 {len(missing)} 条）')
    if extra:
        print(f'  !! 越界索引 {extra[:20]}')
    if missing or extra:
        print('  已中止（请补齐译文）')
        return

    # 索引 -> (path_id, 新译文)；只覆盖提供了译文的行
    want = {}
    for i, sc in tr.items():
        want[rows[i]['path_id']] = restore(sc)

    p = os.path.join(SRC, a, b, '__data')
    env = UnityPy.load(p)
    n = 0
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        sc = want.get(o.path_id)
        if sc is None:
            continue
        t = o.read_typetree()
        t['m_text'] = sc
        o.save_typetree(t)
        n += 1
    print(f'  写回 {n}/{len(want)} 个对象')

    if not write:
        print('  （未写入，加 --write）')
        return

    os.makedirs(OUT, exist_ok=True)
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    print(f'  输出 {dst}  {os.path.getsize(p)} -> {len(raw)} B')


if __name__ == '__main__':
    main()
