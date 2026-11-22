# -*- coding: utf-8 -*-
"""用结构签名序列比对，把译文自动对齐回原文。

背景：手工按行号挂译文时，遇上非假名行（！？、…………。）会跳号，
导致译文整体或局部错位。但译文的书写顺序是对的。

做法：
  JP 侧：每个待译行取签名 (ESC数, 换行数)
  CN 侧：每条译文取签名
  用 DP 做序列对齐（允许插入/删除），把 CN 按对齐结果绑到 JP 行。
对齐后统计残余不符，并输出可人工核对的清单。
"""
import os, sys, json
import importlib.util

ROOT = os.path.dirname(os.path.abspath(__file__))


def load(p, n):
    s = importlib.util.spec_from_file_location(n, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


def restore(s):
    return s.replace('{P}', '\x1bh').replace('{E}', '\x1b')


def sig(s):
    return (s.count('\x1b'), s.count('\n'))


def align(jp_sigs, cn_sigs):
    """返回 CN 索引 -> JP 索引 的映射（最长公共子序列式对齐）。"""
    n, m = len(jp_sigs), len(cn_sigs)
    # dp[i][j] = 前 i 个 JP 与 前 j 个 CN 的最大匹配数
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        di = dp[i]
        pi = dp[i - 1]
        for j in range(1, m + 1):
            if jp_sigs[i - 1] == cn_sigs[j - 1]:
                di[j] = pi[j - 1] + 1
            else:
                di[j] = pi[j] if pi[j] >= di[j - 1] else di[j - 1]
    # 回溯
    mapping = {}
    i, j = n, m
    while i > 0 and j > 0:
        if jp_sigs[i - 1] == cn_sigs[j - 1] and dp[i][j] == dp[i - 1][j - 1] + 1:
            mapping[j - 1] = i - 1
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return mapping


def main():
    bundle = sys.argv[1]
    mods = sys.argv[2:]
    a, b = bundle.split('/')
    rows = [r for r in json.load(open(os.path.join(ROOT, 'lw_work/story_todo2.json'),
                                      encoding='utf-8'))
            if r['a'] == a and r['b'] == b]
    kana = [i for i, r in enumerate(rows) if r['kana']]

    vals = []
    for i, p in enumerate(mods):
        m = load(os.path.join(ROOT, p), f'part{i}')
        d = getattr(m, 'PART_A', None) or getattr(m, 'PART_B', None) or getattr(m, 'SC')
        vals += [d[k] for k in sorted(d)]
    print(f'待译行 {len(kana)}，译文 {len(vals)}')

    jp_sigs = [sig(rows[i]['m_text']) for i in kana]
    cn_sigs = [sig(restore(v)) for v in vals]
    mapping = align(jp_sigs, cn_sigs)
    print(f'对齐成功 {len(mapping)} / {len(vals)}')

    out = {}
    used = set()
    for cj, ji in mapping.items():
        out[kana[ji]] = vals[cj]
        used.add(cj)
    unmatched_cn = [i for i in range(len(vals)) if i not in used]
    unmatched_jp = [kana[i] for i in range(len(kana)) if i not in set(mapping.values())]
    print(f'未能对齐的译文 {len(unmatched_cn)} 条，未覆盖的原文行 {len(unmatched_jp)} 条')
    if unmatched_jp:
        print('  未覆盖行示例:', unmatched_jp[:12])

    # 残余检查
    bad = []
    for idx, v in out.items():
        if sig(rows[idx]['m_text']) != sig(restore(v)):
            bad.append(idx)
    print(f'对齐后结构不符 {len(bad)} 条')

    dst = os.path.join(ROOT, 'lw_work', 'align_out.json')
    json.dump({str(k): v for k, v in out.items()},
              open(dst, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'-> {dst}')


if __name__ == '__main__':
    main()
