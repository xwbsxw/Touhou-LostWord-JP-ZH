# -*- coding: utf-8 -*-
"""对若干「表+字段」统计：日服待译格里的内容，在汉化包 / 国服里分别是什么状态。"""
import os, re, sys, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
trans = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

COMBOS = [('Bullet', 1), ('Bullet', 2), ('SkillEffect', 1), ('SkillEffect', 2),
          ('Voice', 3), ('Resist', 1), ('Spellcard', 1), ('Shot', 1), ('Skill', 1)]

for tname, fi in COMBOS:
    h = NAMES[tname]
    jp = msgpack.unpackb(open(f'dumped/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
    P = msgpack.unpackb(open(f'dl/ext/lwlocal/dec/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
    cpath = f'lw_work/dump_cn/{h}.msgpack'
    C = msgpack.unpackb(open(cpath, 'rb').read(), raw=False, strict_map_key=False) if os.path.exists(cpath) else {}
    tr = trans.get(tname, {})
    st = {'包有中文': 0, '包同原文': 0, '包是英文': 0, '包为空': 0, '包仍是日文': 0, '无此行': 0}
    cn_st = {'国服有中文': 0, '国服无': 0}
    samp = []
    for rid, jr in jp.items():
        if not isinstance(jr, list) or fi >= len(jr):
            continue
        jv = jr[fi]
        if not isinstance(jv, str) or not KANA.search(jv):
            continue
        if str(fi) in tr.get(str(rid), {}):
            continue
        pr = P.get(rid)
        if not isinstance(pr, list) or fi >= len(pr):
            st['无此行'] += 1
            continue
        pv = pr[fi]
        if not isinstance(pv, str) or not pv.strip():
            st['包为空'] += 1
        elif pv.strip() == jv.strip():
            st['包同原文'] += 1
        elif KANA.search(pv):
            st['包仍是日文'] += 1
        elif HAN.search(pv):
            st['包有中文'] += 1
            if len(samp) < 3:
                cr = C.get(rid)
                cv = cr[fi] if isinstance(cr, list) and fi < len(cr) else None
                samp.append((rid, jv, pv, cv))
        else:
            st['包是英文'] += 1
        cr = C.get(rid)
        cv = cr[fi] if isinstance(cr, list) and fi < len(cr) else None
        if isinstance(cv, str) and HAN.search(cv) and not KANA.search(cv):
            cn_st['国服有中文'] += 1
        else:
            cn_st['国服无'] += 1
    tot = sum(st.values())
    print(f'=== {tname}[{fi}]  待译 {tot} ===')
    print('   ' + '  '.join(f'{k}={v}' for k, v in st.items() if v))
    print('   ' + '  '.join(f'{k}={v}' for k, v in cn_st.items()))
    for rid, jv, pv, cv in samp:
        print(f'   [{rid}] 日:{jv[:40]!r}')
        print(f'          包:{pv[:40]!r}  国:{str(cv)[:40]!r}')
    print()
