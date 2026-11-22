# -*- coding: utf-8 -*-
"""从国际服汉化包 (lwlocal v1.4) 抽取可直接搬进日服的中文译文。

原理：
  国际服 1.58 与日服 1.71.1 的主表是同一套数据 —— 同表名、同行 ID、同字段顺序，
  只是文本语言不同。汉化包已把国际服的表「按行只替换文本单元格」成简体中文，
  所以 (表, 行ID, 字段序号) 三元组可以直接对应到日服同一格，再转繁中即可。

安全闸门（任一不满足就丢弃该字段）：
  1. 日服该格含假名（= 待译目标）且当前 trans_all 里还没有译文
  2. 汉化包该格是中文（有汉字、无假名）
  3. 富文本标签名序列完全一致（<color> / <b> / <size> …）
  4. {0} {1} 占位符序号完全一致（否则 string.Format 会抛异常）
  5. ESC 控制符数量一致

输出：
  lw_work/trans_cnpatch.json    {表名: {行ID: {字段序号: 繁中}}}
  lw_work/cnpatch_stats.json    每张表的收获
  lw_work/cnpatch_samples.txt   抽样，供人工抽查
"""
import os, re, json, sys
from collections import Counter
import msgpack
import opencc

ROOT = os.path.dirname(os.path.abspath(__file__))
PATCH_DIR = os.path.join(ROOT, 'dl', 'ext', 'lwlocal', 'dec')
JP_DIR = os.path.join(ROOT, 'dumped')
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
TRANS_ALL = os.path.join(ROOT, 'lw_work', 'trans_all.json')
OUT = os.path.join(ROOT, 'lw_work', 'trans_cnpatch.json')
STATS = os.path.join(ROOT, 'lw_work', 'cnpatch_stats.json')
SAMPLES = os.path.join(ROOT, 'lw_work', 'cnpatch_samples.txt')

KANA = re.compile(r'[\u3040-\u309f\u30a0-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf]')
TAG = re.compile(r'</?([A-Za-z]+)')
PH = re.compile(r'\{(\d+)(?::[^{}]*)?\}')

from lw_cc import cc  # 由 LW_MODE 控制简/繁


def tags(s):
    return sorted(TAG.findall(s))


def phs(s):
    return sorted(PH.findall(s))


def load(p):
    try:
        return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
    except Exception:
        return None


def main():
    trans = json.load(open(TRANS_ALL, encoding='utf-8')) if os.path.exists(TRANS_ALL) else {}
    out, stats, samp = {}, [], {}
    rej = Counter()
    for tname, h in NAMES.items():
        pp, jp = os.path.join(PATCH_DIR, h + '.msgpack'), os.path.join(JP_DIR, h + '.msgpack')
        if not (os.path.exists(pp) and os.path.exists(jp)):
            continue
        P, J = load(pp), load(jp)
        if P is None or J is None:
            continue
        tr = trans.get(tname, {})
        tbl, got = {}, 0
        for rid in set(P) & set(J):
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
                    rej['已有译文'] += 1; continue
                if not KANA.search(jv):
                    rej['日文侧无假名'] += 1; continue
                if KANA.search(pv):
                    rej['补丁侧仍是日文'] += 1; continue
                if not HAN.search(pv):
                    rej['补丁侧无汉字'] += 1; continue
                if pv.strip() == jv.strip():
                    rej['未改动'] += 1; continue
                if tags(jv) != tags(pv):
                    rej['富文本标签不一致'] += 1; continue
                if phs(jv) != phs(pv):
                    rej['占位符不一致'] += 1; continue
                if jv.count('\x1b') != pv.count('\x1b'):
                    rej['控制符不一致'] += 1; continue
                tbl.setdefault(str(rid), {})[str(i)] = cc.convert(pv)
                got += 1
                if len(samp.get(tname, [])) < 4:
                    samp.setdefault(tname, []).append((rid, i, jv, pv))
        if tbl:
            out[tname] = tbl
            stats.append({'table': tname, 'fields': got, 'rows': len(tbl)})

    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    json.dump(stats, open(STATS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    with open(SAMPLES, 'w', encoding='utf-8') as f:
        f.write(f'共 {sum(s["fields"] for s in stats)} 字段 / {len(out)} 张表\n\n')
        for s in sorted(stats, key=lambda x: -x['fields']):
            f.write(f'--- {s["table"]}  +{s["fields"]} 字段 / {s["rows"]} 行 ---\n')
            for rid, i, jv, pv in samp.get(s['table'], []):
                f.write(f'  [{rid}.{i}]\n    日: {jv}\n    中: {pv}\n')
            f.write('\n')

    stats.sort(key=lambda x: -x['fields'])
    total = sum(s['fields'] for s in stats)
    print(f'=== 新增可搬移 {total} 字段 / {len(out)} 张表 ===')
    for s in stats:
        print(f'  {s["table"]:24s} +{s["fields"]:<6} ({s["rows"]} 行)')
    print('\n--- 因闸门丢弃 ---')
    for k, v in rej.most_common(10):
        print(f'  {k:20s} {v}')


if __name__ == '__main__':
    main()
