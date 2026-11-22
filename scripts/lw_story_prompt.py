# -*- coding: utf-8 -*-
"""按序号打印某剧情包的待译行（只数含假名的行），供按序号翻译。

用法: python lw_story_prompt.py <A/B> <起> <迄>
序号从 1 开始。
"""
import os, sys, json

ROOT = os.path.dirname(os.path.abspath(__file__))


def main():
    a, b = sys.argv[1].split('/')
    lo = int(sys.argv[2])
    hi = int(sys.argv[3])
    rows = [r for r in json.load(open(os.path.join(ROOT, 'lw_work/story_todo2.json'),
                                      encoding='utf-8'))
            if r['a'] == a and r['b'] == b]
    need = [r for r in rows if r['kana']]
    print(f'本包待译共 {len(need)} 行；本次输出 {lo}-{hi}')
    for o in range(lo, hi + 1):
        if o > len(need):
            break
        t = need[o - 1]['m_text'].replace('\x1bh', '{P}').replace('\x1b', '{E}')
        print(f'{o}|{t}')


if __name__ == '__main__':
    main()
