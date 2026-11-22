# -*- coding: utf-8 -*-
"""挖出日服 Dynamic TMP 字体引用的源 TTF，用 fontTools 读 cmap，
判断繁体字到底有没有字形（没有就会显示成方块）。"""
import os, sys, json, io, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
JPDIR = os.path.join(ROOT, 'lw_work', 'jpuc')

from fontTools.ttLib import TTFont

found = []   # (bundle_a, font_name, cmap_set or None, nbytes)


def iter_bundles():
    for a in sorted(os.listdir(JPDIR)):
        pa = os.path.join(JPDIR, a)
        if not os.path.isdir(pa):
            continue
        for b in os.listdir(pa):
            f = os.path.join(pa, b, '__data')
            if os.path.exists(f):
                yield a, b, f


for a, b, f in iter_bundles():
    try:
        env = UnityPy.load(f)
    except Exception:
        continue
    # 找动态字体资产
    targets = []
    for obj in env.objects:
        if obj.type.name != 'MonoBehaviour':
            continue
        try:
            tree = obj.read_typetree()
        except Exception:
            continue
        if not isinstance(tree, dict):
            continue
        if 'm_CharacterTable' not in tree or 'm_SourceFontFile' not in tree:
            continue
        if tree.get('m_AtlasPopulationMode') != 1:   # 只要 Dynamic
            continue
        targets.append(tree)
    if not targets:
        continue
    # 收集该包内的 Font / TextAsset 数据，按 path_id
    blobs = {}
    for obj in env.objects:
        if obj.type.name not in ('Font', 'TextAsset'):
            continue
        try:
            d = obj.read()
            data = getattr(d, 'm_FontData', None) or getattr(d, 'm_Script', None)
            if isinstance(data, bytes) and len(data) > 1000:
                blobs[obj.path_id] = data
        except Exception:
            pass
    if not blobs:
        continue
    for tree in targets:
        ref = tree.get('m_SourceFontFile') or {}
        pid = ref.get('m_PathID') if isinstance(ref, dict) else None
        raw = blobs.get(pid)
        name = tree.get('m_Name', '?')
        cmap = None
        if raw:
            try:
                tt = TTFont(io.BytesIO(raw), fontNumber=0, lazy=True)
                cmap = set()
                for t in tt['cmap'].tables:
                    cmap |= set(t.cmap.keys())
                tt.close()
            except Exception:
                cmap = None
        found.append((a, name, cmap, len(raw) if raw else 0))
        if len(found) >= 8:
            break
    if len(found) >= 8:
        break

print(f'解析到动态字体源 {len(found)} 个\n')
TEST = ('裡纔於為個們來說時間過後門問題點電腦車馬龍龜鬱鑑齋籲爨響'
        '麗靈夢藍紫魔理沙博麗霊夢詠唱結界彈幕符卡')
for a, name, cmap, n in found:
    if cmap is None:
        print(f'  {name[:40]}  ({n} B)  cmap 读取失败/无源文件')
        continue
    miss = [c for c in TEST if ord(c) not in cmap]
    print(f'  {name[:40]}  ({n} B)  cmap {len(cmap)} 字')
    print(f'      缺字形: {"".join(miss) if miss else "无（全覆盖）"}')

allc = set()
for _, _, c, _ in found:
    if c:
        allc |= c
if allc:
    miss = [c for c in TEST if ord(c) not in allc]
    print(f'\n合并覆盖 {len(allc)} 字； 测试集中缺失: {"".join(miss) if miss else "无"}')
    json.dump(sorted(allc), open(os.path.join(ROOT, 'lw_work', 'jp_font_cmap.json'), 'w'))
