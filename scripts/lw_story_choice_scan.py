# -*- coding: utf-8 -*-
"""扫描主线剧情包里所有 MonoBehaviour 的脚本类与文本字段，
找出「主角选项」的载体（TalkOrder/MessageOrder 之外，可能含 choice/select 字段）。
"""
import os, json, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
ASCII = re.compile(r'[A-Za-z]{3,}')

MAIN = [
    ('48696ed27f68c8acd4ae91fcfd1ad6cb', '1d2d470e27aa6bc9e5e2a1b272c7e2c6'),
    ('580339df439f3804b452f0120b0854d0', 'f1b3616d93c0177db247fb42ae622dbf'),
    ('359f1d36f245cd68b87dbfaf9058ec92', 'b4dfaae3c99fce9525f61ceca3bb1bf9'),
]

cls_fields = collections.defaultdict(set)
field_samples = collections.defaultdict(list)

for a, b in MAIN:
    p = os.path.join(SRC, a, b, '__data')
    if not os.path.exists(p):
        continue
    env = UnityPy.load(p)
    cls = {}
    for o in env.objects:
        if o.type.name == 'MonoScript':
            try:
                cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
            except Exception:
                pass
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not isinstance(t, dict):
            continue
        sp = t.get('m_Script') or {}
        cn = cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None
        # 只看有文本字段的
        for k, v in t.items():
            if isinstance(v, str) and v.strip() and len(v) >= 2:
                if k in ('m_Script', 'm_GameObject'):
                    continue
                cls_fields[cn].add(k)
                if len(field_samples[(cn, k)]) < 3:
                    field_samples[(cn, k)].append(v[:40])

print('=== 剧情包里含文本字段的脚本类（除 TalkOrder/MessageOrder）===')
for cn, fields in sorted(cls_fields.items()):
    if cn in ('TalkOrder', 'MessageOrder'):
        continue
    if not fields:
        continue
    print(f'\n[{cn}] 字段: {sorted(fields)}')
    for k in sorted(fields):
        for s in field_samples.get((cn, k), []):
            print(f'    {k}: {s!r}')
