# -*- coding: utf-8 -*-
"""诊断：剩余待译串里，有多少可以「拆成已知词条」自动拼出来。"""
import os, json, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
NAME_EXACT = json.load(open(os.path.join(ROOT, 'lw_work', 'names_exact.json'), encoding='utf-8'))
KANA = re.compile(r'[\u3040-\u30ff]')
w = json.load(open(os.path.join(ROOT, 'lw_work', 'work_visible.json'), encoding='utf-8'))

print(f'names_exact.json 词条 {len(NAME_EXACT)}')
for probe in ('吉弔八千慧', '歩く漢方薬', '八雲藍', '妹の心、姉知らず', '博麗霊夢', '八意永琳'):
    print(f'  查 {probe!r:26} -> {NAME_EXACT.get(probe)!r}')

print('\n=== 各字段可拆分情况 ===')
for tbl in ('Bullet', 'Shot', 'Mission', 'Episode', 'Section', 'VoiceSet', 'Enemy', 'Resist', 'ValuePackShop'):
    for fi, items in sorted(w.get(tbl, {}).items(), key=lambda x: -sum(n for _, n in x[1]))[:2]:
        tot = sum(n for _, n in items)
        # 尝试：整串 / 「A_B C」拆分 / 「A(B)C」拆分
        whole = sum(n for s, n in items if s in NAME_EXACT)
        print(f'  {tbl}[{fi}]  唯一 {len(items):<5} 总计 {tot:<5} 整串命中 {whole}')
