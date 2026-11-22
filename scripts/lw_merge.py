#!/usr/bin/env python3
"""合并多份译文 json（后面的覆盖前面的），输出 lw_work/trans_all.json。"""
import json, os, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(ROOT, 'lw_work', 'trans_cn_tw.json')
CNPATCH = os.path.join(ROOT, 'lw_work', 'trans_cnpatch.json')
NAMES = os.path.join(ROOT, 'lw_work', 'trans_names.json')
TM = os.path.join(ROOT, 'lw_work', 'trans_tm.json')
RULES = os.path.join(ROOT, 'lw_work', 'trans_rules.json')
MANUAL = os.path.join(ROOT, 'lw_work', 'trans_manual.json')
OUT = os.path.join(ROOT, 'lw_work', 'trans_all.json')


def main():
    from lw_cc import to_simplified, MODE
    out = {}
    # 优先级从低到高：模板套用 < 国服原文 < 国际服汉化包 < 名词表 < 规则 < 人工
    # 说明：国服原文/汉化包/名词表/模板 在 LW_MODE=sc 下已是简体；
    #       规则层已在 lw_rules 内部转简体；只有人工层需要在这里转。
    for p in [TM, BASE, CNPATCH, NAMES, RULES, MANUAL]:
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        needs_sc = (p == MANUAL and MODE == 'sc')
        for tbl, rows in d.items():
            t = out.setdefault(tbl, {})
            for k, fields in rows.items():
                if needs_sc:
                    fields = {i: to_simplified(v) for i, v in fields.items()}
                t.setdefault(k, {}).update(fields)
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    n_tbl = len(out)
    n_row = sum(len(v) for v in out.values())
    n_f = sum(len(f) for v in out.values() for f in v.values())
    print(f'{n_tbl} 张表 / {n_row} 条 / {n_f} 字段 -> {OUT}')


if __name__ == '__main__':
    main()
