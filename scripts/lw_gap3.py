# -*- coding: utf-8 -*-
"""用「国服自己翻不翻这一格」当可见性判据，估算真正还需要翻的玩家可见文本。

逻辑：我的流水线已经把国服所有中文格子都吃干净了。
      剩下的格里，如果国服同格也是日文（== 原文），说明连官方简体客户端都不翻它
      —— 极可能是内部标识（如 博麗霊夢-スペカA1 / 八意永琳 - ラスワ / 春っぽい何か）。
      这类不该算进「玩家可见待译」。
"""
import os, re, json, msgpack
from lw_visible import visible_field, is_internal

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
trans = json.load(open(os.path.join(ROOT, 'lw_work', 'trans_all.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

tot = {'cn有中文': 0, '国服同文': 0, '国服无此行': 0, '国服其他': 0}
per = {}
for tname, h in NAMES.items():
    jp = os.path.join(ROOT, 'dumped', h + '.msgpack')
    cp = os.path.join(ROOT, 'lw_work', 'dump_cn', h + '.msgpack')
    if not os.path.exists(jp):
        continue
    J = msgpack.unpackb(open(jp, 'rb').read(), raw=False, strict_map_key=False)
    C = msgpack.unpackb(open(cp, 'rb').read(), raw=False, strict_map_key=False) if os.path.exists(cp) else {}
    tr = trans.get(tname, {})
    st = dict.fromkeys(tot, 0)
    for rid, jr in J.items():
        if not isinstance(jr, list):
            continue
        trr = tr.get(str(rid), {})
        for i, jv in enumerate(jr):
            if not isinstance(jv, str) or not KANA.search(jv) or str(i) in trr:
                continue
            if not visible_field(tname, i) or is_internal(jv):
                continue
            cr = C.get(rid)
            cv = cr[i] if isinstance(cr, list) and i < len(cr) else None
            if not isinstance(cv, str) or not cv.strip():
                k = '国服无此行'
            elif HAN.search(cv) and not KANA.search(cv):
                k = 'cn有中文'
            elif cv.strip() == jv.strip():
                k = '国服同文'
            else:
                k = '国服其他'
            st[k] += 1
    if any(st.values()):
        per[tname] = st
        for k in tot:
            tot[k] += st[k]

print(f'{"表":20s} {"cn有中文":>8s} {"国服同文":>8s} {"国服无此行":>10s} {"国服其他":>8s} {"小计":>8s}')
for t, st in sorted(per.items(), key=lambda x: -sum(x[1].values()))[:20]:
    print(f'{t:20s} {st["cn有中文"]:>8d} {st["国服同文"]:>8d} {st["国服无此行"]:>10d} {st["国服其他"]:>8d} {sum(st.values()):>8d}')
print('-' * 62)
print(f'{"合计":20s} {tot["cn有中文"]:>8d} {tot["国服同文"]:>8d} {tot["国服无此行"]:>10d} {tot["国服其他"]:>8d} {sum(tot.values()):>8d}')
print()
print(f'→ 真正需要翻（排除「国服自己也不翻」的内部串）≈ {tot["cn有中文"] + tot["国服其他"]}')
