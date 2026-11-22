# -*- coding: utf-8 -*-
"""数据完整性总检查：对比 dumped/(日文原版) 与 out/(已汉化)，
找出会破坏游戏逻辑的字段改动：
  1. 原版是合法 JSON，译文却不是合法 JSON
  2. 原版是纯数字串，译文不是
  3. 译文为空/纯空白
  4. 原文无占位符但译文新增了占位符（string.Format 会抛异常）
  5. 富文本标签增删
"""
import os, sys, re, json, msgpack

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

PH = re.compile(r'\{(\d+)(?::[^{}]*)?\}')
TAG = re.compile(r'</?([A-Za-z][A-Za-z0-9]*)')
NUM = re.compile(r'^-?\d+(\.\d+)?$')

names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))

problems = []
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
            # 1. JSON
            js = j.strip()
            if js[:1] in ('{', '['):
                try:
                    json.loads(j)
                    ok_j = True
                except Exception:
                    ok_j = False
                if ok_j:
                    try:
                        json.loads(o)
                    except Exception as e:
                        problems.append(('JSON破损', tn, k, i, j[:60], o[:60], str(e)[:40]))
                        continue
            # 2. 纯数字
            if NUM.match(js):
                if not NUM.match(o.strip()):
                    problems.append(('数字破坏', tn, k, i, j[:40], o[:40], ''))
                    continue
            # 3. 空
            if not o.strip():
                problems.append(('空字符串', tn, k, i, j[:40], repr(o), ''))
                continue
            # 4. 新增占位符
            if not PH.search(j) and PH.search(o):
                problems.append(('新增占位符', tn, k, i, j[:40], o[:40], ''))
                continue
            # 5. 标签
            if sorted(TAG.findall(j)) != sorted(TAG.findall(o)):
                problems.append(('标签不一致', tn, k, i, j[:40], o[:40], ''))

print(f'共发现 {len(problems)} 处问题\n')
from collections import Counter
c = Counter(p[0] for p in problems)
for k, v in c.most_common():
    print(f'  {k:10} {v}')
print()
for p in problems[:25]:
    print(f'[{p[0]}] {p[1]} id={p[2]} f={p[3]}')
    print(f'    日: {p[4]!r}')
    print(f'    中: {p[5]!r} {p[6]}')
