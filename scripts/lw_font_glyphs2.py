# -*- coding: utf-8 -*-
"""在含字体资产的包里直接找 Font / TextAsset 里的原始 TTF，读 cmap 判断字形覆盖。"""
import os, sys, json, io
import UnityPy
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.abspath(__file__))
JPDIR = os.path.join(ROOT, 'lw_work', 'jpuc')
meta = json.load(open(os.path.join(ROOT, 'lw_work', 'jp_fonts.json'), encoding='utf-8'))
pkgs = sorted({(f['a'], f['b']) for f in meta['fonts']})
print(f'字体相关包 {len(pkgs)} 个')

results = []
for a, b in pkgs:
    f = os.path.join(JPDIR, a, b, '__data')
    if not os.path.exists(f):
        continue
    try:
        env = UnityPy.load(f)
    except Exception:
        continue
    for obj in env.objects:
        if obj.type.name not in ('Font', 'TextAsset'):
            continue
        try:
            d = obj.read()
        except Exception:
            continue
        raw = getattr(d, 'm_FontData', None)
        if not isinstance(raw, bytes):
            raw = getattr(d, 'm_Script', None)
        if not isinstance(raw, bytes) or len(raw) < 5000:
            continue
        if raw[:4] not in (b'\x00\x01\x00\x00', b'true', b'OTTO', b'ttcf'):
            continue
        try:
            tt = TTFont(io.BytesIO(raw), fontNumber=0, lazy=True)
            cm = set()
            for t in tt['cmap'].tables:
                cm |= set(t.cmap.keys())
            tt.close()
        except Exception:
            continue
        results.append((a, getattr(d, 'm_Name', '?'), len(raw), cm))

print(f'解出 TTF {len(results)} 个')
for a, n, sz, cm in results:
    print(f'  {n[:34]:34s} {sz:>9} B  cmap {len(cm)}')

allc = set()
for _, _, _, c in results:
    allc |= c
if allc:
    TEST = ('裡纔於為個們來說時間過後門問題點電腦車馬龍龜鬱齋籲爨響'
            '麗靈夢藍紫魔理沙博麗詠唱結界彈幕符卡歸言錄東方法')
    miss = [c for c in TEST if ord(c) not in allc]
    print(f'\n合并 cmap {len(allc)} 字')
    print(f'测试集缺字形: {"".join(miss) if miss else "无（全覆盖）"}')
    json.dump(sorted(allc), open(os.path.join(ROOT, 'lw_work', 'jp_font_cmap.json'), 'w'))
    print('已保存 -> lw_work/jp_font_cmap.json')
else:
    print('没找到任何能解析的 TTF —— 需要换思路（字体可能在别的共享包）')
