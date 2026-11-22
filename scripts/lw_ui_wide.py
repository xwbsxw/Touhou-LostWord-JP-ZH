# -*- coding: utf-8 -*-
"""广域扫描：找出所有字符串字段里含目标 UI 文字的对象，并给出层级路径。

与之前的区别：
 - 不限 LocalizeText，任何 MonoBehaviour / GameObject 名字 / Text 都看
 - 输出 m_Name 与 m_GameObject 路径，便于判断哪个是真正渲染的实例
"""
import os, sys, json, re
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
ROOTDIR = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, 'dev_jp', 'shared')
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ROOT, 'lw_work/jp_ui_wide.json')
WANT = ['フレンド', 'ショップ', 'おいのり']


def gopath(env_cache, treemap, mgo):
    """顺 m_GameObject -> m_Father 拼路径"""
    names = []
    cur = mgo
    for _ in range(12):
        if cur is None:
            break
        d = treemap.get(cur)
        if not d:
            break
        names.append(d.get('m_Name', '?'))
        cur = d.get('m_Father', {}).get('m_PathID') if isinstance(d.get('m_Father'), dict) else None
    return '/'.join(reversed(names))


def main():
    keys = []
    for a in sorted(os.listdir(ROOTDIR)):
        pa = os.path.join(ROOTDIR, a)
        if not os.path.isdir(pa):
            continue
        for b in os.listdir(pa):
            f = os.path.join(pa, b, '__data')
            if os.path.exists(f):
                keys.append((a, b, f))
    print(f'待扫 {len(keys)} 包', flush=True)

    found = []
    for i, (a, b, f) in enumerate(keys):
        if i % 400 == 0:
            print(f'  {i}/{len(keys)}  命中 {len(found)}', flush=True)
        try:
            env = UnityPy.load(f)
        except Exception:
            continue
        # 先缓存 GameObject 层级树
        gos = {}
        need = False
        for o in env.objects:
            if o.type.name != 'GameObject':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            gos[o.path_id] = t
        for o in env.objects:
            if o.type.name not in ('MonoBehaviour', 'GameObject'):
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            hit = []
            for k, v in t.items():
                if isinstance(v, str) and v.strip() in WANT:
                    hit.append((k, v))
            if not hit:
                continue
            mgo = t.get('m_GameObject')
            pid = mgo.get('m_PathID') if isinstance(mgo, dict) else None
            found.append({
                'a': a, 'b': b, 'path_id': o.path_id, 'type': o.type.name,
                'm_Name': t.get('m_Name'),
                'go_path': gopath(env, gos, pid),
                'hits': hit,
                'fields': {k: t.get(k) for k in
                           ('m_Text', 'enText', 'jpText', 'showingLanguage')
                           if k in t},
            })
            print(f'  HIT {a[:8]} {o.type.name:12} {t.get("m_Name")!r} '
                  f'{hit} path={gopath(env, gos, pid)}', flush=True)

    json.dump(found, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'\n共命中 {len(found)} 个对象 -> {OUT}')


if __name__ == '__main__':
    main()
