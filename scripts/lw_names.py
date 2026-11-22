#!/usr/bin/env python3
"""角色名 / 专有名词 繁中化。

国服的 Person 表里人名仍是日文（博麗霊夢），所以没法像其他表那样直接抄。
做法：
  1. 从全表对齐对里挖 (日文, 国服简体) 名词对 —— 例如 ArenaEnemy 里
     「ルーミア」→「露米娅」、「博麗霊夢」→「博丽灵梦」；
  2. 名字整体命中 → 直接用；否则用**字级映射**（霊→灵、麗→丽…）逐字替换；
  3. 统一 s2twp 转繁中。

输出 lw_work/trans_names.json，格式与 lw_patch.py 一致。
"""
import os, sys, json, re, collections, msgpack
import opencc

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_cc import cc  # 由 LW_MODE 控制简/繁

NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
PAIRS_PATH = os.path.join(ROOT, 'lw_work', 'name_pairs.json')
OUT = os.path.join(ROOT, 'lw_work', 'trans_names.json')

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\uf900-\ufaff]')
BAD = re.compile(r'[<>{}%0-9\n]')


def load_pairs():
    raw = json.load(open(PAIRS_PATH, encoding='utf-8'))
    pairs = {}
    for k, v in raw.items():
        jp, cn = k.split('\u0000')
        pairs[(jp, cn)] = v
    return pairs


def build_maps(pairs):
    """整串映射 + 字级映射（只保留高置信度）"""
    name_map = {}
    char_votes = collections.defaultdict(collections.Counter)
    for (jp, cn), n in pairs.items():
        if BAD.search(jp) or BAD.search(cn):
            continue
        if len(jp) > 16 or len(cn) > 16:
            continue
        name_map.setdefault(jp, collections.Counter())[cn] += n
        if len(jp) == len(cn):
            for a, b in zip(jp, cn):
                if a != b and (KANA.search(a) or HAN.search(a)) and HAN.search(b):
                    char_votes[a][b] += n
    name_map = {k: v.most_common(1)[0][0] for k, v in name_map.items()}
    char_map = {}
    for a, votes in char_votes.items():
        b, n = votes.most_common(1)[0]
        tot = sum(votes.values())
        if n >= 2 and n / tot >= 0.6:
            char_map[a] = b
    return name_map, char_map


def convert_name(name, name_map, char_map):
    if name in name_map:
        return cc.convert(name_map[name]), 'dict'
    # 只有「纯汉字名」才逐字转，含假名的混排一律不动，避免产生半通不通的夹生文本
    if KANA.search(name):
        return None, 'kana'
    out = []
    ok = 0
    for ch in name:
        if ch in char_map:
            out.append(char_map[ch])
            ok += 1
        else:
            out.append(ch)
    if ok == 0:
        return None, 'none'
    return cc.convert(''.join(out)), 'charmap'


def main():
    pairs = load_pairs()
    name_map, char_map = build_maps(pairs)
    print(f'整串映射 {len(name_map)} 条，字级映射 {len(char_map)} 字')

    out = {}
    stat = collections.Counter()
    for tbl in ['Person', 'Enemy', 'ArenaEnemy']:
        h = NAMES.get(tbl)
        if not h or not os.path.exists(os.path.join(ROOT, 'dumped', h + '.msgpack')):
            continue
        jp = msgpack.unpackb(open(os.path.join(ROOT, 'dumped', h + '.msgpack'), 'rb').read(),
                             raw=False, strict_map_key=False)
        rows = {}
        for k, jv in jp.items():
            if not isinstance(jv, list):
                continue
            fields = {}
            for i, x in enumerate(jv):
                if not isinstance(x, str) or not (2 <= len(x) <= 16):
                    continue
                if not (KANA.search(x) or HAN.search(x)) or BAD.search(x):
                    continue
                tw, how = convert_name(x, name_map, char_map)
                if not tw or tw == x:
                    stat[how] += 1
                    continue
                fields[str(i)] = tw
                stat[how + '_ok'] += 1
            if fields:
                rows[str(k)] = fields
        if rows:
            out[tbl] = rows
    print('统计', dict(stat))
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    for tbl, rows in out.items():
        n = sum(len(f) for f in rows.values())
        print(f'  {tbl}: {len(rows)} 条 / {n} 字段')
        for k, f in list(rows.items())[:3]:
            print('    ', k, f)


if __name__ == '__main__':
    main()
