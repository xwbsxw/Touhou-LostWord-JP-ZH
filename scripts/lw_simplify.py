# -*- coding: utf-8 -*-
"""把 trans_all.json 里的繁体文本转成简体（t2s），保留含假名的日文残留。

用法: python lw_simplify.py
- 备份原 trans_all.json -> trans_all.bak.json
- 只转「不含假名 + t2s 有变化」的文本字段
- 输出简体 trans_all.json
"""
import os, sys, json, re
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
T2S = OpenCC('t2s')
KANA = re.compile(r'[\u3040-\u30ff]')
CJK = re.compile(r'[\u4e00-\u9fff]')

SRC = os.path.join(ROOT, 'lw_work', 'trans_all.json')
BAK = os.path.join(ROOT, 'lw_work', 'trans_all.bak.json')

d = json.load(open(SRC, encoding='utf-8'))
changed = 0
for tbl, rows in d.items():
    for k, fields in rows.items():
        for i, v in list(fields.items()):
            if not isinstance(v, str) or not v.strip():
                continue
            if KANA.search(v):
                continue  # 日文残留，不转
            if not CJK.search(v):
                continue
            s = T2S.convert(v)
            if s != v:
                fields[i] = s
                changed += 1

if not os.path.exists(BAK):
    json.dump(json.load(open(SRC, encoding='utf-8')), open(BAK, 'w', encoding='utf-8'),
              ensure_ascii=False)
    print(f'已备份原文件 -> {BAK}')

json.dump(d, open(SRC, 'w', encoding='utf-8'), ensure_ascii=False)
print(f'繁改简完成：转换 {changed} 个字段')
