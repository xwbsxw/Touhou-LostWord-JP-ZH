#!/usr/bin/env python3
"""人工译文层：读 lw_work/manual_trans.json（日文原句 → 繁中译文），套用到所有表。

这是所有层里优先级最高的——只要 manual_trans.json 里写了，就一定覆盖。
长尾文本靠这个一点点补：往 json 里加条目，重跑本脚本即可。

格式：
{
  "月属性+陰気寄り": "月屬性+偏陰氣",
  "基本に必中": "基礎附加必中"
}
"""
import os, sys, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
MANUAL = os.path.join(ROOT, 'lw_work', 'manual_trans.json')
OUT = os.path.join(ROOT, 'lw_work', 'trans_manual.json')


def main():
    if not os.path.exists(MANUAL):
        json.dump({}, open(MANUAL, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(f'已创建空表 {MANUAL}')
        return
    manual = json.load(open(MANUAL, encoding='utf-8'))
    print(f'人工词条 {len(manual)} 条')
    out = {}
    hit = 0
    for tbl, h in sorted(NAMES.items()):
        p = os.path.join(ROOT, 'dumped', h + '.msgpack')
        if not os.path.exists(p):
            continue
        jp = msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
        if not isinstance(jp, dict):
            continue
        rows = {}
        for k, jv in jp.items():
            if not isinstance(jv, list):
                continue
            for i, x in enumerate(jv):
                if not isinstance(x, str):
                    continue
                tw = manual.get(x)
                if tw and tw != x:
                    rows.setdefault(str(k), {})[str(i)] = tw
                    hit += 1
        if rows:
            out[tbl] = rows
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'人工层命中 {hit} 字段 -> {OUT}')


if __name__ == '__main__':
    main()
