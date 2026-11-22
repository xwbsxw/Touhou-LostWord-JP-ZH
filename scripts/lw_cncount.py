# -*- coding: utf-8 -*-
"""国服（简体官方）每张表每个字段里，究竟有多少格是中文？——判断该字段到底是不是「官方会本地化」的字段。"""
import os, re, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

TABLES = ['Bullet', 'SkillEffect', 'Voice', 'Skill', 'Spellcard', 'Shot',
          'Resist', 'Person', 'Enemy', 'Picture', 'Ability', 'Characteristic']

for tname in TABLES:
    h = NAMES[tname]
    cp = f'lw_work/dump_cn/{h}.msgpack'
    if not os.path.exists(cp):
        print(f'{tname}: 无国服数据')
        continue
    C = msgpack.unpackb(open(cp, 'rb').read(), raw=False, strict_map_key=False)
    jp = msgpack.unpackb(open(f'dumped/{h}.msgpack', 'rb').read(), raw=False, strict_map_key=False)
    nf = max((len(v) for v in C.values() if isinstance(v, list)), default=0)
    out = []
    for i in range(nf):
        cn = jp_ = 0
        for v in C.values():
            if isinstance(v, list) and i < len(v) and isinstance(v[i], str) and v[i].strip():
                if HAN.search(v[i]) and not KANA.search(v[i]):
                    cn += 1
                else:
                    jp_ += 1
        if cn or jp_:
            out.append((i, cn, jp_))
    print(f'=== {tname}  国服行 {len(C)} ===')
    for i, cn, other in out:
        tag = ' ← 官方会本地化' if cn > other else ''
        print(f'   [{i}] 中文 {cn:<6} 非中文 {other:<6}{tag}')
    print()
