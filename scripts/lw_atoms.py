# -*- coding: utf-8 -*-
"""把剩余待译串拆成「原子词条」，按权重排序 —— 翻 300 个原子胜过翻 4000 个整串。

原子提取规则：
  Bullet[1] / Shot[2]  「称号_角色 ショットA」  -> 称号、角色
  Mission[2]           「Tをクリアしよう」等    -> T
  Episode[4]           「T」第N回 / 最終回      -> T
  ValuePackShop[6]     「Tが入ったお得なパック」-> T
  其余整串当作原子
"""
import os, json, re, collections

ROOT = os.path.dirname(os.path.abspath(__file__))
w = json.load(open(os.path.join(ROOT, 'lw_work', 'work_visible.json'), encoding='utf-8'))

RE_SLOT = re.compile(r'^(.+?)[ 　]*(ショット|スペカ|ラスワ)([AB])?$')
RE_M = [re.compile(p) for p in (
    r'^(.+?)を1日\d+回クリアしよう$', r'^(.+?)を\d+回クリアしよう$',
    r'^(.+?)を\d+回完了させよう$', r'^(.+?)を\d+つクリアしよう$',
    r'^(.+?)で\d+回勝利しよう$', r'^(.+?)の★を\d+個取ろう$',
    r'^(.+?)の★を全て取ろう$', r'^(.+?)を完了させよう$',
    r'^(.+?)をクリアしよう$', r'^(.+?)をクリア$')]
RE_EP = [re.compile(p) for p in (
    r'^(.+?)第(\d+)回$', r'^(.+?)最終回$', r'^(.+?)[ 　・]+プロローグ$',
    r'^(.+?)[ 　・]+エピローグ$', r'^(.+?)[ 　]+(\d+)日目$', r'^EX[ 　]+(.+)$')]
RE_PACK = re.compile(r'^(.+?)が入ったお得な(パック|セット)$')

atoms = collections.Counter()
for tbl, fields in w.items():
    for fi, items in fields.items():
        for s, n in items:
            got = []
            m = RE_SLOT.match(s)
            if m and tbl in ('Bullet', 'Shot'):
                got = [m.group(1)]
            elif tbl == 'Mission':
                for p in RE_M:
                    mm = p.match(s)
                    if mm:
                        got = [mm.group(1)]
                        break
            elif tbl in ('Episode', 'Chapter'):
                for p in RE_EP:
                    mm = p.match(s)
                    if mm:
                        got = [mm.group(1)]
                        break
            elif tbl == 'ValuePackShop':
                mm = RE_PACK.match(s)
                if mm:
                    got = [mm.group(1)]
            if not got:
                got = [s]
            for a in got:
                for part in a.split('_'):
                    atoms[part.strip()] += n

json.dump(dict(atoms), open(os.path.join(ROOT, 'lw_work', 'atoms.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=0)
print(f'原子词条 {len(atoms)}  权重合计 {sum(atoms.values())}')
print()
for a, n in atoms.most_common(150):
    print(f'{n:>4}  {a[:80]}')
