# -*- coding: utf-8 -*-
"""对齐测试：国际服汉化包 vs 日服主表，看按 (表, 行ID, 字段) 能直接搬多少条中文过来。"""
import os, sys, json, re
import msgpack

KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')

patch_dir = 'dl/ext/lwlocal/dec'
jp_dir = 'dumped'
trans = json.load(open('lw_work/trans_all.json', encoding='utf-8'))
names = json.load(open('lw_work/table_names.json', encoding='utf-8'))

def load(path):
    try:
        return msgpack.unpackb(open(path, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None

tot_gain = 0
report = []
for tname, h in names.items():
    pp = os.path.join(patch_dir, h + '.msgpack')
    jp = os.path.join(jp_dir, h + '.msgpack')
    if not (os.path.exists(pp) and os.path.exists(jp)):
        continue
    P = load(pp); J = load(jp)
    if P is None or J is None:
        continue
    tr = trans.get(tname, {})
    common = set(P) & set(J)
    gain = 0
    samples = []
    for rid in common:
        pr, jr = P[rid], J[rid]
        if not isinstance(pr, list) or not isinstance(jr, list):
            continue
        trr = tr.get(str(rid), {})
        for i in range(min(len(pr), len(jr))):
            jv, pv = jr[i], pr[i]
            if not isinstance(jv, str) or not isinstance(pv, str):
                continue
            if not jv.strip() or not pv.strip():
                continue
            if str(i) in trr:
                continue                      # 已有译文
            if not KANA.search(jv):           # 日文行里没有假名 → 不是待译目标
                continue
            if KANA.search(pv) or not HAN.search(pv):
                continue                      # 汉化包这一格不是中文
            if pv.strip() == jv.strip():
                continue
            gain += 1
            if len(samples) < 2:
                samples.append((rid, i, jv[:44], pv[:44]))
    if gain:
        tot_gain += gain
        report.append((tname, gain, len(common), len(J), samples))

report.sort(key=lambda x: -x[1])
print(f'=== 可搬移总量 {tot_gain} 字段 ===\n')
for tname, gain, nc, nj, samples in report:
    print(f'{tname:26s} +{gain:<7} (共同行 {nc}/{nj})')
    for rid, i, jv, pv in samples:
        print(f'    [{rid}.{i}] 日: {jv}')
        print(f'             中: {pv}')
