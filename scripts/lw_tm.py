#!/usr/bin/env python3
"""模板记忆库（Translation Memory）：用国服已翻好的同模板句子，套到还没翻的句子上。

原理：技能/弹幕说明高度模板化，例如
  日「自身の<color=#CCAA00>CRI攻撃</color>を7段階<color=#FF6600>アップ</color> (2T)」
  中「自身<color=#CCAA00>會心攻擊</color><color=#FF6600>上升</color>7等級 (2回合)」
把数字抽掉变成骨架，就能一对多复用：
  日骨架「自身の<color=##>CRI攻撃</color>を#段階…アップ</color> (#T)」
  中骨架「自身<color=##>會心攻擊</color><color=##>上升</color>#等級 (#回合)」

用法：
  python lw_tm.py build      # 建库 -> lw_work/tm.json
  python lw_tm.py apply      # 套用到剩余字段 -> lw_work/trans_tm.json
"""
import os, sys, json, re, glob, msgpack, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import opencc

ROOT = os.path.dirname(os.path.abspath(__file__))
NAMES = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
TM_PATH = os.path.join(ROOT, 'lw_work', 'tm.json')
OUT = os.path.join(ROOT, 'lw_work', 'trans_tm.json')
from lw_cc import cc  # 由 LW_MODE 控制简/繁

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff\uf900-\ufaff]')
JPX = re.compile(r'[\u3040-\u30ff\u4e00-\u9fff\uf900-\ufaff]')
NUM = re.compile(r'\d+(?:\.\d+)?')

JP_DIR = os.path.join(ROOT, 'dumped')
CN_DIR = os.path.join(ROOT, 'lw_work', 'dump_cn')


def load(h, side):
    d = JP_DIR if side == 'jp' else CN_DIR
    p = os.path.join(d, h + '.msgpack')
    if not os.path.exists(p):
        return None
    return msgpack.unpackb(open(p, 'rb').read(), raw=False, strict_map_key=False)


COLOR = re.compile(r'<color=#[0-9A-Fa-f]{6}>')


def mask_colors(s):
    """把 <color=#RRGGBB> 换成不带数字的 <color>，并记录原色值，避免进制数字被当成数值"""
    colors = []

    def repl(m):
        colors.append(m.group(0))
        return '<color>'

    return COLOR.sub(repl, s), colors


def unmask_colors(s, colors):
    out = []
    it = iter(colors)
    for part in s.split('<color>'):
        out.append(part)
        out.append(next(it, '<color>'))
    return ''.join(out[:-1]) if colors else s


def skeleton(s):
    masked, _ = mask_colors(s)
    return NUM.sub('#', masked)


def build():
    tm = collections.defaultdict(collections.Counter)
    n_pairs = 0
    for tbl, h in sorted(NAMES.items()):
        jp, cn = load(h, 'jp'), load(h, 'cn')
        if not isinstance(jp, dict) or not isinstance(cn, dict):
            continue
        for k, jv in jp.items():
            cv = cn.get(k)
            if not isinstance(cv, list) or not isinstance(jv, list):
                continue
            for i, x in enumerate(jv):
                if not isinstance(x, str) or not JPX.search(x):
                    continue
                if i >= len(cv) or not isinstance(cv[i], str):
                    continue
                c = cv[i]
                if not c or c == x or not HAN.search(c):
                    continue
                if x.count('#') or c.count('#'):
                    continue
                n_pairs += 1
                tm[skeleton(x)][c] += 1
    out = {}
    for sk, votes in tm.items():
        c, n = votes.most_common(1)[0]
        out[sk] = (c, n)
    json.dump(out, open(TM_PATH, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'对齐样本 {n_pairs}，模板 {len(out)} 条 -> {TM_PATH}')
    # 示例
    for sk, (c, n) in list(out.items())[:5]:
        print(f'  x{n}  {sk[:60]}\n      -> {c[:60]}')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'build'
    if cmd == 'build':
        build()
        return
    tm = json.load(open(TM_PATH, encoding='utf-8'))
    # 只跳过「国服原文 / 名词表」已经覆盖的字段，模板库自己算出来的结果不能反过来当输入
    trans = {}
    for p in ('trans_cn_tw.json', 'trans_names.json'):
        fp = os.path.join(ROOT, 'lw_work', p)
        if not os.path.exists(fp):
            continue
        d = json.load(open(fp, encoding='utf-8'))
        for tbl, rows in d.items():
            t = trans.setdefault(tbl, {})
            for k, f in rows.items():
                t.setdefault(k, {}).update(f)
    out = {}
    hit = miss = 0
    for tbl, h in sorted(NAMES.items()):
        jp = load(h, 'jp')
        if not isinstance(jp, dict):
            continue
        done = trans.get(tbl, {})
        rows = {}
        for k, jv in jp.items():
            if not isinstance(jv, list):
                continue
            df = done.get(str(k), {})
            fields = {}
            for i, x in enumerate(jv):
                if not isinstance(x, str) or not JPX.search(x) or str(i) in df:
                    continue
                sk = skeleton(x)
                ent = tm.get(sk)
                if not ent:
                    miss += 1
                    continue
                cn, n = ent
                masked_jp, _ = mask_colors(x)
                masked_cn, cn_colors = mask_colors(cn)
                nums = NUM.findall(masked_jp)
                if len(nums) != len(NUM.findall(masked_cn)):
                    miss += 1
                    continue
                it = iter(nums)
                res = NUM.sub(lambda m: next(it), masked_cn)
                res = unmask_colors(res, cn_colors)
                rows.setdefault(str(k), {})[str(i)] = cc.convert(res)
                hit += 1
            if not fields and rows.get(str(k)):
                pass
        if rows:
            out[tbl] = rows
    # 清理空表
    out = {t: {k: v for k, v in rows.items() if v} for t, rows in out.items()}
    out = {t: rows for t, rows in out.items() if rows}
    json.dump(out, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False)
    print(f'模板命中 {hit} 字段，未命中 {miss} -> {OUT}')


if __name__ == '__main__':
    main()
