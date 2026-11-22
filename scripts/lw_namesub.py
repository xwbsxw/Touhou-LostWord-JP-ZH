#!/usr/bin/env python3
"""专有名词替换层：把长串里夹着的日文角色名/道具名换成繁中。

名字表来自 `lw_work/name_pairs.json`（国服对照里挖出的 日文名→简体名），
只替换长度 >= 2 的整词，长词优先，避免把短名字片段乱替换。
"""
import os, sys, json, re, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import opencc

NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'lw_work', 'trans_namesub.json')
from lw_cc import cc  # 由 LW_MODE 控制简/繁

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\uf900-\ufaff]')
JPX = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uf900-\ufaff]')
BAD = re.compile(r'[<>{}%]')


def load_name_map():
    raw = json.load(open(os.path.join(ROOT, 'lw_work', 'name_pairs.json'), encoding='utf-8'))
    votes = {}
    for k, v in raw.items():
        jp, cn = k.split('\u0000')
        if len(jp) < 2 or len(jp) > 16 or BAD.search(jp) or BAD.search(cn):
            continue
        votes.setdefault(jp, {})[cn] = votes.setdefault(jp, {}).get(cn, 0) + v
    out = {}
    for jp, d in votes.items():
        cn = max(d, key=d.get)
        if cn != jp:
            out[jp] = cc.convert(cn)
    return out


def substitute(text, name_map):
    """在字符串里做最长匹配替换：逐位置尝试 4~16 字的子串，命中就用最长的那条。"""
    n = len(text)
    out = []
    i = 0
    changed = False
    while i < n:
        best = None
        for ln in range(min(16, n - i), 1, -1):
            sub = text[i:i + ln]
            if sub in name_map:
                best = sub
                break
        if best:
            rep = name_map[best]
            if rep != best:
                out.append(rep)
                changed = True
                i += len(best)
                continue
        out.append(text[i])
        i += 1
    return ''.join(out), changed


def main():
    name_map = load_name_map()
    print(f'名字表 {len(name_map)} 条')
    base = {}
    for p in ('trans_cn_tw.json', 'trans_names.json', 'trans_tm.json', 'trans_rules.json'):
        fp = os.path.join(ROOT, 'lw_work', p)
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp, encoding='utf-8'))
        for tbl, rows in d.items():
            t = base.setdefault(tbl, {})
            for k, f in rows.items():
                t.setdefault(k, {}).update(f)

    out = {}
    hit = 0
    for tbl, h in sorted(NAMES.items()):
        p = os.path.join(ROOT, 'dumped', h + '.msgpack')
        if not os.path.exists(p):
            continue
        jp = msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)
        if not isinstance(jp, dict):
            continue
        done = base.get(tbl, {})
        rows = {}
        for k, jv in jp.items():
            if not isinstance(jv, list):
                continue
            df = done.get(str(k), {})
            for i, x in enumerate(jv):
                if not isinstance(x, str) or not JPX.search(x) or str(i) in df:
                    continue
                y, changed = substitute(x, name_map)
                if not changed or y == x:
                    continue
                rows.setdefault(str(k), {})[str(i)] = y
                hit += 1
        if rows:
            out[tbl] = rows
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'名词替换命中 {hit} 字段 -> {OUT}')
    for tbl, rows in list(out.items())[:4]:
        for k, f in list(rows.items())[:2]:
            print(' ', tbl, k, f)


if __name__ == '__main__':
    main()
