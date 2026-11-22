# -*- coding: utf-8 -*-
"""语义级数据校验：
  1. 日文原版是 JSON → 解析后必须与译文 JSON 深度相等（不只是"合法"）
  2. 原文看起来是标识符/键名（纯 ASCII 小写+下划线）→ 译文不应变成中文
  3. 原文是路径 → 译文必须相同
"""
import os, sys, re, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
IDENT = re.compile(r'^[A-Za-z_][A-Za-z0-9_]*$')
PATH = re.compile(r'^[\w/.\-]+\.(png|prefab|ogg|mat|asset|json|txt|xml|bytes)$', re.I)

names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
issues = []

for fn in sorted(os.listdir(os.path.join(ROOT, 'out'))):
    if not fn.endswith('.bin'):
        continue
    tn = fn[:-4]
    h = names.get(tn)
    if not h:
        continue
    jp_path = os.path.join(ROOT, 'dumped', h + '.msgpack')
    if not os.path.exists(jp_path):
        continue
    jp = msgpack.unpackb(open(jp_path, 'rb').read(), raw=False, strict_map_key=False)
    ou = msgpack.unpackb(decrypt(open(os.path.join(ROOT, 'out', fn), 'rb').read()),
                         raw=False, strict_map_key=False)
    for k, jv in jp.items():
        ov = ou.get(k)
        if not isinstance(jv, list) or not isinstance(ov, list):
            continue
        for i in range(min(len(jv), len(ov))):
            j, o = jv[i], ov[i]
            if not isinstance(j, str) or not isinstance(o, str) or j == o:
                continue
            js = j.strip()
            # 1. JSON 语义相等
            if js[:1] in ('{', '['):
                try:
                    a = json.loads(j)
                except Exception:
                    a = None
                if a is not None:
                    try:
                        b = json.loads(o)
                    except Exception:
                        issues.append(('JSON非法', tn, k, i, j[:50], o[:50]))
                        continue
                    if a != b:
                        issues.append(('JSON语义变化', tn, k, i, j[:50], o[:50]))
                        continue
            # 2. 标识符被翻译
            if IDENT.match(js) and HAN.search(o):
                issues.append(('标识符被译', tn, k, i, j[:50], o[:50]))
                continue
            # 3. 路径被改
            if PATH.match(js) and j != o:
                issues.append(('路径被改', tn, k, i, j[:50], o[:50]))
                continue

from collections import Counter
print(f'共 {len(issues)} 处')
for k, v in Counter(x[0] for x in issues).most_common():
    print(f'  {k:14} {v}')
print()
for x in issues[:20]:
    print(f'[{x[0]}] {x[1]} id={x[2]} f={x[3]}')
    print(f'    日: {x[4]!r}')
    print(f'    中: {x[5]!r}')
