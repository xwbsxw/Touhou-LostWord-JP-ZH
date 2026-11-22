# -*- coding: utf-8 -*-
"""判定性实验：把主页「フレンド」按钮的三字段写成不同内容，看界面显示哪个。

    jpText  -> 好友J
    m_Text  -> 好友M
    enText  -> 好友E

结果直接告诉我们在日服上应该改哪个字段。
"""
import os, sys, json
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, 'dev_jp/shared/8df5deee82aa5ccf71066fb3cca05917/'
                          '7d7a6a8bb250a1c30f00e535551f6535/__data')
OUT = os.path.join(ROOT, 'lw_work/uitest')
TARGET = 'フレンド'

os.makedirs(OUT, exist_ok=True)
env = UnityPy.load(SRC)

report = []
for o in env.objects:
    if o.type.name != 'MonoBehaviour':
        continue
    try:
        t = o.read_typetree()
    except Exception:
        continue
    if not isinstance(t, dict):
        continue
    hit = False
    if t.get('jpText') == TARGET:
        t['jpText'] = '好友J'
        hit = True
    if t.get('m_Text') == TARGET:
        t['m_Text'] = '好友M'
        hit = True
    if t.get('enText') == TARGET:
        t['enText'] = '好友E'
        hit = True
    if hit:
        o.save_typetree(t)
        report.append({'path_id': o.path_id, 'keys': sorted(t.keys())})

print(f'改动 {len(report)} 个对象')
for r in report:
    print(f'  path_id={r["path_id"]}  keys={r["keys"]}')

dst = os.path.join(OUT, '8df5deee82aa5ccf71066fb3cca05917__7d7a6a8bb250a1c30f00e535551f6535__data')
raw = env.file.save(packer='original')
open(dst, 'wb').write(raw)
print(f'输出 {dst}  {len(raw)} B (原 {os.path.getsize(SRC)} B)')
