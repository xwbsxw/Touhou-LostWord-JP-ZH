# -*- coding: utf-8 -*-
"""校验重新打包的剧情包：
1) 能否被 UnityPy 正常加载
2) 对象总数 / 各类型计数是否与原包一致
3) MessageOrder 条数是否一致
4) m_text 是否确为繁中、无假名
5) 其他字段（m_attr 等）是否原样
"""
import os, sys, json, collections, re
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc')
OUT = os.path.join(ROOT, 'lw_work', 'story_out')
KANA = re.compile(r'[\u3041-\u309f\u30a0-\u30fa\u30fc-\u30ff]')

stat = json.load(open(os.path.join(ROOT, 'lw_work', 'story_out_stat.json'), encoding='utf-8'))
ok = True

for s in stat:
    a, b = s['bundle'].split('/')
    f_src = os.path.join(SRC, a, b, '__data')
    f_out = os.path.join(OUT, f'{a}__{b}__data')

    def survey(p):
        env = UnityPy.load(p)
        types = collections.Counter(o.type.name for o in env.objects)
        msg = []
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            t = o.read_typetree()
            if 'm_text' in t and 'm_name' in t and 'm_attr' in t:
                msg.append(t)
        return env, types, msg

    e1, t1, m1 = survey(f_src)
    e2, t2, m2 = survey(f_out)

    print(f'=== {a[:10]}… ===')
    print(f'  对象数: {sum(t1.values())} -> {sum(t2.values())}')
    print(f'  类型分布一致: {dict(t1) == dict(t2)}')
    if dict(t1) != dict(t2):
        print('    src:', dict(t1))
        print('    out:', dict(t2))
        ok = False
    print(f'  MessageOrder: {len(m1)} -> {len(m2)}')
    if len(m1) != len(m2):
        ok = False

    # 逐条比对 m_attr 未变，m_text 已变
    changed = same = 0
    for x, y in zip(m1, m2):
        if x.get('m_attr') != y.get('m_attr') or x.get('m_PathID') != y.get('m_PathID'):
            print('    ! 非文本字段被改动')
            ok = False
        if x.get('m_text') == y.get('m_text'):
            same += 1
        else:
            changed += 1
    kana = [y['m_text'][:30] for y in m2 if KANA.search(y['m_text'])]
    print(f'  m_text 已改 {changed}, 未改 {same}, 残留假名 {len(kana)}')
    if kana:
        print('    ', kana[:3])
        ok = False
    # 抽样
    for y in m2[:2]:
        print(f'    [{y.get("m_name")}] {y["m_text"][:46]!r}')

print('\n总体:', 'PASS' if ok else 'FAIL')
