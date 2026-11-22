# -*- coding: utf-8 -*-
"""把国服 FZYaSong-B-GBK 字体数据注入日服的两个字体包。

只替换 Font.m_FontData，其余（资源名、FontNames、字号、升部、容器路径、
Texture2D、Material）全部保持日服原样。
输出到 lw_work/font_out/。
"""
import os, json, hashlib
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
FONTDATA = os.path.join(ROOT, 'lw_work', 'cn_font_fontdata.bin')
OUT = os.path.join(ROOT, 'lw_work', 'font_out')

TARGETS = [
    ('8e26f7cd3502423bcaa899485d1ef294', '6118ba7ff546c9b2fcb0dc64e84547fe'),
    ('314db829d8c817469b7b016950eedc3e', '4f7a28726011db3e8c19e2da6e271e53'),
]

new_data = open(FONTDATA, 'rb').read()
print(f'注入字体 {len(new_data)} B  头={new_data[:8]!r}')
os.makedirs(OUT, exist_ok=True)

report = []
for a, b in TARGETS:
    src = os.path.join(ROOT, 'dev_jp', 'shared', a, b, '__data')
    env = UnityPy.load(src)
    old_len = old_head = None
    done = 0
    for o in env.objects:
        if o.type.name != 'Font':
            continue
        d = o.read()
        fd = getattr(d, 'm_FontData', None)
        if isinstance(fd, list):
            fd = bytes(fd)
        old_len = len(fd) if fd else 0
        old_head = (fd or b'')[:4]
        d.m_FontData = list(new_data)
        d.save()
        done += 1
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    report.append(dict(a=a, b=b, replaced=done,
                       old_len=old_len, old_head=old_head.hex(),
                       src_size=os.path.getsize(src), dst_size=len(raw),
                       dst_md5=hashlib.md5(raw).hexdigest()))
    print(f'  {a[:10]}…  替换 {done} 个 Font  '
          f'旧 {old_len} B({old_head!r})  {os.path.getsize(src)} -> {len(raw)} B')

json.dump(report, open(os.path.join(ROOT, 'lw_work', 'font_out_report.json'), 'w',
                       encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n完成 ->', OUT)
