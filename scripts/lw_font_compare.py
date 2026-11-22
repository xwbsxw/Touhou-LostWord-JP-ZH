# -*- coding: utf-8 -*-
"""比对国服(v1.5)与日服的字体包结构：Unity 版本、对象类型、TMP 字体资产名与字形覆盖。"""
import os, struct, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))

PAIRS = [
    ('A', 'dl/v15/fonts/A_cn_font.bundle',
     'dev_jp/shared/8e26f7cd3502423bcaa899485d1ef294/6118ba7ff546c9b2fcb0dc64e84547fe/__data'),
    ('B', 'dl/v15/fonts/B_cn_font.bundle',
     'dev_jp/shared/314db829d8c817469b7b016950eedc3e/4f7a28726011db3e8c19e2da6e271e53/__data'),
]

# 简体专用字（日文字体通常没有）
SIMP = '们说这个时过问题电车门马龙龟齐响应对开关闭选择确认继续'
# 日文特有（判断是否日文字体）
JPONLY = '々ゝゞヶ'


def header(p):
    with open(p, 'rb') as f:
        sig = f.read(8)
        ver = struct.unpack('>I', f.read(4))[0]

        def cstr():
            b = b''
            while True:
                c = f.read(1)
                if not c or c == b'\x00':
                    return b.decode('utf-8', 'replace')
                b += c
        uv = cstr()
        ur = cstr()
        f.read(8)
        f.read(4)
        f.read(4)
        flags = struct.unpack('>I', f.read(4))[0]
    return dict(ver=ver, unity=uv, rev=ur, flags=hex(flags))


def survey(p, label):
    print(f'--- {label} ---')
    h = header(p)
    print(f'  UnityFS v{h["ver"]}  unity={h["unity"]}  rev={h["rev"]}  flags={h["flags"]}')
    env = UnityPy.load(p)
    types = collections.Counter(o.type.name for o in env.objects)
    print(f'  对象: {dict(types)}')
    fonts = []
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not isinstance(t, dict) or 'm_AtlasPopulationMode' not in t:
            continue
        chars = t.get('m_CharacterTable') or []
        codes = {c.get('m_Unicode') for c in chars
                 if isinstance(c, dict) and isinstance(c.get('m_Unicode'), int)}
        fonts.append(dict(name=t.get('m_Name'), mode=t.get('m_AtlasPopulationMode'),
                          nchars=len(chars), w=t.get('m_AtlasWidth'), h=t.get('m_AtlasHeight'),
                          fallbacks=len(t.get('m_FallbackFontAssetTable') or []),
                          codes=codes))
    for f in fonts:
        print(f'  字体资产 {f["name"]!r}')
        print(f'     mode={f["mode"]} 字形={f["nchars"]} 图集={f["w"]}x{f["h"]} '
              f'fallback={f["fallbacks"]} 码位={len(f["codes"])}')
    return fonts


allf = {}
for tag, cnp, jpp in PAIRS:
    print(f'===== 组 {tag} =====')
    cn = survey(os.path.join(ROOT, cnp), f'CN-{tag}')
    jp = survey(os.path.join(ROOT, jpp), f'JP-{tag}')
    cn_names = [f['name'] for f in cn]
    jp_names = [f['name'] for f in jp]
    print(f'  资源名一致: {sorted(cn_names) == sorted(jp_names)}')
    if cn_names != jp_names:
        print(f'    CN: {cn_names}')
        print(f'    JP: {jp_names}')
    print()
    allf[tag] = (cn, jp)

print('=== 简体字覆盖 ===')
for tag, (cn, jp) in allf.items():
    cnall = set().union(*[f['codes'] for f in cn]) if cn else set()
    jpall = set().union(*[f['codes'] for f in jp]) if jp else set()
    miss_cn = [c for c in SIMP if ord(c) not in cnall]
    miss_jp = [c for c in SIMP if ord(c) not in jpall]
    print(f'  组{tag}: CN 共{len(cnall)}码位  日文特有无={[c for c in JPONLY if ord(c) in cnall]}')
    print(f'        简体测试字 CN缺 {"".join(miss_cn) or "无"}')
    print(f'        简体测试字 JP缺 {"".join(miss_jp) or "无"}')
