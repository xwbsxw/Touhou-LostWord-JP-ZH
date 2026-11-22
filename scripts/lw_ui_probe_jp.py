# -*- coding: utf-8 -*-
"""在日服 bundle 里找界面文字（ショップ/仲間/絵札…），并 dump LocalizeText 三字段，
用来判定日服客户端读的是 m_Text / enText / jpText 哪一个。

用法: python lw_ui_probe_jp.py <bundle_root> <out.json>
"""
import os, sys, json, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
TARGETS = ['ショップ', '仲間', '絵札', '施設', '課題', 'おいのり',
           'フレンド', '図鑑', '素材', '伝書', '告知', 'メニュー']


def walk_str(o, out, prefix=''):
    if isinstance(o, str):
        out.append((prefix, o))
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in ('m_Script', 'm_GameObject'):
                continue
            walk_str(v, out, f'{prefix}.{k}' if prefix else k)
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            walk_str(v, out, f'{prefix}[{i}]')


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
    print(f'待扫 {len(keys)} 个包', flush=True)

    findings = []
    for i, (a, b, f) in enumerate(keys):
        if i % 300 == 0:
            print(f'  {i}/{len(keys)}  命中 {len(findings)}', flush=True)
        try:
            env = UnityPy.load(f)
        except Exception:
            continue
        # 先便宜地看 MonoScript 类名
        cls = {}
        try:
            for o in env.objects:
                if o.type.name == 'MonoScript':
                    cls[o.path_id] = getattr(o.read(), 'm_ClassName', '') or ''
        except Exception:
            continue
        if not cls:
            continue
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            if not ({'m_Text', 'enText', 'jpText'} & set(t.keys())):
                continue
            sv = []
            walk_str(t, sv)
            hit = sorted({w for w in TARGETS if any(w in s for _, s in sv)})
            if not hit:
                continue
            sp = t.get('m_Script') or {}
            pid = sp.get('m_PathID') if isinstance(sp, dict) else None
            findings.append({
                'a': a, 'b': b, 'path_id': o.path_id,
                'script': cls.get(pid, '?'),
                'keys': sorted(t.keys()),
                'hit': hit,
                'm_Text': t.get('m_Text'),
                'enText': t.get('enText'),
                'jpText': t.get('jpText'),
                'showing': {k: v for k, v in t.items()
                            if 'anguage' in k or 'how' == k[:4]},
            })

    json.dump(findings, open(outp, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'\n命中 {len(findings)} 个 LocalizeText 组件 -> {outp}')

    # 摘要：日服侧三字段分别是什么
    print('\n=== 三字段对照（前 25 条）===')
    for r in findings[:25]:
        print(f'  [{r["script"]}] 命中{r["hit"]}')
        print(f'     m_Text={r["m_Text"]!r}')
        print(f'     enText={r["enText"]!r}')
        print(f'     jpText={r["jpText"]!r}')
        if r['showing']:
            print(f'     lang 相关字段={r["showing"]}')


if __name__ == '__main__':
    main()
