#!/usr/bin/env python3
"""用国服（简体）master 数据自动生成繁中译文。

原理：国服 6.6.0 与日服 1.71.1 的 master 表 **同表名、同 id、同字段顺序**
（已用 Picture 之外全部表验证）。国服已经翻译过的字段直接拿来，转成繁體後回写日服。

输出：
  lw_work/trans_cn_tw.json   {表名: {id: {字段序号: 繁體中文}}}   —— 给 lw_patch.py 用
  lw_work/autocn_stats.json  每张表覆盖情况

用法：
  python lw_autocn.py              # 生成译文
  python lw_autocn.py --list       # 只看统计
"""
import os, sys, json, glob, re, argparse, msgpack

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opencc

ROOT = os.path.dirname(os.path.abspath(__file__))
JP_DIR = os.path.join(ROOT, 'dumped')
CN_DIR = os.path.join(ROOT, 'lw_work', 'dump_cn')
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'lw_work', 'trans_cn_tw.json')
STATS = os.path.join(ROOT, 'lw_work', 'autocn_stats.json')

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\uf900-\ufaff]')
# 需要翻译的字段：含假名（日文）或纯汉字（人名/道具名等，国服用简体汉字写）
JPX = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uf900-\ufaff]')
# string.Format 占位符：{0} / {1:0.0} —— 国服译文里的占位符必须是日文占位符的子集，
# 否则游戏里 string.Format 会抛 FormatException（很可能就是整表一推就卡死/闪退的原因）
PH = re.compile(r'\{(\d+)(?::[^{}]*)?\}')

from lw_cc import cc  # 由 LW_MODE 控制简/繁

# 游戏术语修正（opencc 之后统一）——保持与速查表一致
FIX = {
    '幻想鄉': '幻想鄉',
    '博麗靈夢': '博麗靈夢',
    '結界異常': '結界異常',
    '靈力': '靈力',
    '御札': '御札',
    '繪札': '繪札',
    '符卡': '符卡',
    '擦彈': '擦彈',
    '仇恨值': '仇恨值',
}


def tw(s: str) -> str:
    return cc.convert(s)


def load(h, side):
    d = JP_DIR if side == 'jp' else CN_DIR
    p = os.path.join(d, h + '.msgpack')
    if not os.path.exists(p):
        return None
    return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)


def best_offset(jp, cn):
    """极少数表字段数不同（如 Picture 多一列），用文本命中率挑偏移"""
    scores = {}
    for off in (0, 1, -1):
        hit = tot = 0
        for k, jv in list(jp.items())[:300]:
            cv = cn.get(k)
            if not isinstance(cv, list):
                continue
            for i, x in enumerate(jv):
                if isinstance(x, str) and KANA.search(x):
                    j = i + off
                    if 0 <= j < len(cv) and isinstance(cv[j], str) and cv[j] and cv[j] != x and HAN.search(cv[j]):
                        hit += 1
                    tot += 1
        scores[off] = (hit / tot) if tot else 0
    return max(scores, key=scores.get)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--list', action='store_true')
    ap.add_argument('--minlen', type=int, default=0)
    a = ap.parse_args()

    pack = {}
    stats = []
    for name, h in sorted(NAMES.items()):
        jp = load(h, 'jp')
        cn = load(h, 'cn')
        if not isinstance(jp, dict) or not isinstance(cn, dict):
            continue
        off = 0
        # 字段数不一致时才猜偏移
        mism = sum(1 for k in list(jp)[:200] if k in cn and len(cn[k]) != len(jp[k]))
        if mism > 3:
            off = best_offset(jp, cn)
        rows = {}
        total = got = skipped = 0
        for k, jv in jp.items():
            if not isinstance(jv, list):
                continue
            cv = cn.get(k)
            if not isinstance(cv, list):
                continue
            fields = {}
            for i, x in enumerate(jv):
                if not isinstance(x, str) or not JPX.search(x):
                    continue
                total += 1
                j = i + off
                if not (0 <= j < len(cv)) or not isinstance(cv[j], str):
                    continue
                c = cv[j]
                if not c or c == x or not HAN.search(c):
                    continue
                # 占位符安全：国服用到的 {n} 必须都存在于日文串里，否则格式化时会崩
                jph = {m.group(1) for m in PH.finditer(x)}
                cph = {m.group(1) for m in PH.finditer(c)}
                if not cph <= jph:
                    skipped += 1
                    continue
                t = tw(c)
                if t != x:
                    fields[str(i)] = t
                    got += 1
            if fields:
                rows[str(k)] = fields
        if rows:
            pack[name] = rows
        stats.append(dict(table=name, entries=len(jp), fields=total, translated=got,
                          skipped=skipped, offset=off,
                          cov=round(got / total, 3) if total else 0))

    if not a.list:
        json.dump(pack, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(stats, open(STATS, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        n = sum(len(v) for v in pack.values())
        f = sum(len(fe) for v in pack.values() for fe in v.values())
        print(f'{len(pack)} 张表 / {n} 条记录 / {f} 个字段 -> {OUT}')
    stats.sort(key=lambda r: -r['fields'])
    print(f'{"表":30}{"记录":>8}{"日文字段":>9}{"可译":>8}{"覆盖":>7}{"偏移":>5}')
    for s in stats:
        if s['translated']:
            print(f'{s["table"]:30}{s["entries"]:>8}{s["fields"]:>9}{s["translated"]:>8}{s["cov"]*100:>6.1f}%{s["offset"]:>5}')


if __name__ == '__main__':
    main()
