# -*- coding: utf-8 -*-
"""检查字体包内 Font 对象：名称、字体族名、字符矩形数量、图集尺寸。"""
import os
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
PAIRS = [
    ('A', 'dl/v15/fonts/A_cn_font.bundle',
     'dev_jp/shared/8e26f7cd3502423bcaa899485d1ef294/6118ba7ff546c9b2fcb0dc64e84547fe/__data'),
    ('B', 'dl/v15/fonts/B_cn_font.bundle',
     'dev_jp/shared/314db829d8c817469b7b016950eedc3e/4f7a28726011db3e8c19e2da6e271e53/__data'),
]


def probe(p, label):
    env = UnityPy.load(p)
    print(f'--- {label} ---')
    for o in env.objects:
        if o.type.name == 'Font':
            d = o.read()
            names = getattr(d, 'm_FontNames', None)
            chars = getattr(d, 'm_CharacterRects', None)
            fdata = getattr(d, 'm_FontData', None)
            print(f'  Font  名称={getattr(d, "m_Name", "?")!r}')
            print(f'        字体族={names}')
            print(f'        m_CharacterRects={len(chars) if chars else 0}')
            print(f'        m_FontData={len(fdata) if isinstance(fdata, bytes) else fdata}'
                  f'  typ={type(fdata).__name__}')
        elif o.type.name == 'Texture2D':
            d = o.read()
            w = getattr(d, 'm_Width', '?')
            h = getattr(d, 'm_Height', '?')
            fmt = getattr(d, 'm_TextureFormat', '?')
            print(f'  Texture2D 名称={getattr(d, "m_Name", "?")!r}  {w}x{h} fmt={fmt}')
        elif o.type.name == 'Material':
            d = o.read()
            print(f'  Material 名称={getattr(d, "m_Name", "?")!r}')
        elif o.type.name == 'AssetBundle':
            d = o.read()
            print(f'  AssetBundle 名称={getattr(d, "m_Name", "?")!r}')
            cont = getattr(d, 'm_Container', None) or []
            for k, _ in cont:
                print(f'       容器: {k}')
            deps = getattr(d, 'm_Dependencies', None) or []
            if deps:
                print(f'       依赖: {deps}')
    print()


for tag, cnp, jpp in PAIRS:
    print(f'===== 组 {tag} =====')
    probe(os.path.join(ROOT, cnp), f'CN-{tag}')
    probe(os.path.join(ROOT, jpp), f'JP-{tag}')
