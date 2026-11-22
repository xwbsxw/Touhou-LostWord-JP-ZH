# -*- coding: utf-8 -*-
"""从国服字体包提取 m_FontData（原始字体文件），并用 fontTools 检查字符覆盖。"""
import os, io
import UnityPy
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.abspath(__file__))
CN = os.path.join(ROOT, 'dl/v15/fonts/A_cn_font.bundle')
DST = os.path.join(ROOT, 'lw_work', 'cn_font_fontdata.bin')
REP = os.path.join(ROOT, 'lw_work', 'cn_font_coverage.txt')

env = UnityPy.load(CN)
data = None
for o in env.objects:
    if o.type.name != 'Font':
        continue
    d = o.read()
    fd = getattr(d, 'm_FontData', None)
    if isinstance(fd, list):
        data = bytes(fd)
    elif isinstance(fd, (bytes, bytearray)):
        data = bytes(fd)
    break

assert data, '未取到 m_FontData'
open(DST, 'wb').write(data)
print(f'写出 {DST}  {len(data)} B  头={data[:8]!r}')

tt = TTFont(io.BytesIO(data), fontNumber=0, lazy=True)
cmap = set()
for t in tt['cmap'].tables:
    cmap |= set(t.cmap.keys())
name = tt['name']
def nm(nid):
    for r in name.names:
        if r.nameID == nid:
            try:
                return r.toUnicode()
            except Exception:
                pass
    return '?'
info = [
    f'字体文件: {len(data)} B',
    f'家族名: {nm(1)}',
    f'子族名: {nm(2)}',
    f'完整名: {nm(4)}',
    f'版本: {nm(5)}',
    f'表: {sorted(tt.keys())}',
    f'是否 CFF: {"CFF " in tt or "CFF2" in tt}',
    f'是否 glyf: {"glyf" in tt}',
    f'cmap 码位总数: {len(cmap)}',
]
open(REP, 'w', encoding='utf-8').write('\n'.join(info) + '\n')
print('\n'.join(info))

# 关键测试
SIMPLIFIED = '们说这个时过问题电车门马龙龟齐响应对开关闭选择确认继续'
TRADITIONAL = '們說這個時過問題電車門馬龍龜齊響應對開關閉選擇確認繼續'
JAPANESE = '々ゝゞヶ々'
def test(chars, label):
    miss = [c for c in chars if ord(c) not in cmap]
    rep = f'{label}: 缺 {len(miss)} / {len(chars)}  -> {"".join(miss) if miss else "全覆盖"}'
    open(REP, 'a', encoding='utf-8').write(rep + '\n')
    print(rep)

test(SIMPLIFIED, '简体测试')
test(TRADITIONAL, '繁体测试')
test(JAPANESE, '日文假名')

# CJK 覆盖量统计
cjk = [c for c in cmap if 0x4E00 <= c <= 0x9FFF]
ext_a = [c for c in cmap if 0x3400 <= c <= 0x4DBF]
kana = [c for c in cmap if 0x3040 <= c <= 0x30FF]
line = f'CJK基本区 {len(cjk)} / 20992, 扩展A {len(ext_a)}, 假名 {len(kana)}'
open(REP, 'a', encoding='utf-8').write(line + '\n')
print(line)
