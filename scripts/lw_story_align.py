# -*- coding: utf-8 -*-
"""把日服 3 个剧情包与国服 180 个剧情包做对齐，尝试复用已有中文翻译。

思路：
1) 先按「包内 MessageOrder 条数」筛选候选（同场景通常条数一致）
2) 对候选做逐条对齐打分：日文与中文共享大量汉字，用汉字集合的 Jaccard 相似度
3) 输出每条的匹配结果与置信度
"""
import os, sys, json, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
jp = json.load(open(os.path.join(ROOT, 'lw_work', 'jp_story.json'), encoding='utf-8'))
cn = json.load(open(os.path.join(ROOT, 'lw_work', 'cn_story.json'), encoding='utf-8'))

HAN = re.compile(r'[\u4e00-\u9fff]')
KANA = re.compile(r'[\u3040-\u30ff]')


def han_set(s):
    return set(HAN.findall(s))


def sim(a, b):
    """汉字集合 Jaccard；再叠加长度比惩罚"""
    A, B = han_set(a), han_set(b)
    if not A or not B:
        return 0.0
    j = len(A & B) / len(A | B)
    lr = min(len(a), len(b)) / max(len(a), len(b))
    return j * (0.5 + 0.5 * lr)


# 按包归组
def group(rows):
    g = collections.OrderedDict()
    for r in rows:
        k = f"{r['a']}/{r['b']}"
        g.setdefault(k, []).append(r)
    return g


jpb = group(jp)
cnb = group(cn)
print(f'日服剧情包 {len(jpb)} 个, 国服剧情包 {len(cnb)} 个\n')

cn_by_len = collections.defaultdict(list)
for k, v in cnb.items():
    cn_by_len[len(v)].append(k)

report = {}
for k, rows in jpb.items():
    n = len(rows)
    cands = cn_by_len.get(n, [])
    print(f'=== 日服包 {k[:12]}…  {n} 条 ===')
    if not cands:
        # 放宽到 ±5%
        for ln, ks in cn_by_len.items():
            if abs(ln - n) <= max(3, n // 20):
                cands += ks
        print(f'  无同条数候选，放宽范围后 {len(cands)} 个候选')
    best = None
    for ck in cands:
        crows = cnb[ck]
        # 顺序对齐（等长时直接逐条比）
        if len(crows) == n:
            sc = sum(sim(a['text'], b['text']) for a, b in zip(rows, crows)) / n
        else:
            sc = 0.0
        if best is None or sc > best[0]:
            best = (sc, ck)
    if best:
        print(f'  最佳候选 {best[1][:12]}…  平均相似度 {best[0]:.3f}')
        report[k] = {'cn': best[1], 'score': best[0], 'n': n}

print('\n=== 汇总 ===')
for k, v in report.items():
    flag = '可复用' if v['score'] > 0.55 else ('需复核' if v['score'] > 0.35 else '无法复用')
    print(f"  {k[:12]}…  ->  {v['cn'][:12]}…  {v['score']:.3f}  {flag}")

json.dump(report, open(os.path.join(ROOT, 'lw_work', 'story_align.json'), 'w',
                       encoding='utf-8'), ensure_ascii=False, indent=1)
