# -*- coding: utf-8 -*-
"""把字体包的关键信息写入文件（不直接打印字节数组）。"""
import os, json, hashlib
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, 'lw_work', 'font_report.txt')
PAIRS = [
    ('A', 'dl/v15/fonts/A_cn_font.bundle',
     'dev_jp/shared/8e26f7cd3502423bcaa899485d1ef294/6118ba7ff546c9b2fcb0dc64e84547fe/__data'),
    ('B', 'dl/v15/fonts/B_cn_font.bundle',
     'dev_jp/shared/314db829d8c817469b7b016950eedc3e/4f7a28726011db3e8c19e2da6e271e53/__data'),
]

lines = []


def w(s=''):
    lines.append(s)


for tag, cnp, jpp in PAIRS:
    w(f'===== 组 {tag} =====')
    for label, p in (('CN', cnp), ('JP', jpp)):
        w(f'--- {label}: {os.path.getsize(p)} B  md5={hashlib.md5(open(p,"rb").read()).hexdigest()[:12]}')
        env = UnityPy.load(p)
        for o in env.objects:
            if o.type.name == 'Font':
                d = o.read()
                fd = getattr(d, 'm_FontData', None)
                cr = getattr(d, 'm_CharacterRects', None) or []
                w(f'  Font 名={getattr(d, "m_Name", "?")!r}')
                w(f'       m_FontNames={getattr(d, "m_FontNames", None)}')
                w(f'       m_FontSize={getattr(d, "m_FontSize", None)} '
                  f'lineSpacing={getattr(d, "m_LineSpacing", None)} '
                  f'ascent={getattr(d, "m_Ascent", None)}')
                n = len(fd) if isinstance(fd, (bytes, list)) else 0
                w(f'       m_FontData 长度={n} 类型={type(fd).__name__}')
                if n:
                    b = bytes(fd) if isinstance(fd, list) else fd
                    w(f'       文件头={b[:8]!r}')
                    w(f'       FontData md5={hashlib.md5(b).hexdigest()[:16]}')
                w(f'       m_CharacterRects={len(cr)}')
            elif o.type.name == 'Texture2D':
                d = o.read()
                w(f'  Texture2D 名={getattr(d, "m_Name", "?")!r} '
                  f'{getattr(d, "m_Width", "?")}x{getattr(d, "m_Height", "?")} '
                  f'fmt={getattr(d, "m_TextureFormat", "?")} '
                  f'complete={getattr(d, "m_CompleteImageSize", "?")} '
                  f'streamed={getattr(d, "m_StreamData", None) is not None}')
            elif o.type.name == 'AssetBundle':
                d = o.read()
                cont = getattr(d, 'm_Container', None) or []
                names = []
                for k, _ in cont:
                    if k not in names:
                        names.append(k)
                w(f'  AssetBundle 容器={names}')
        w()

open(OUT, 'w', encoding='utf-8').write('\n'.join(lines))
print('written', OUT, len(lines), 'lines')
