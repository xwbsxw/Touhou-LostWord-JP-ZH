# -*- coding: utf-8 -*-
"""把国服同键界面包的 enText（中文）桥接进 jpText，让日服真正显示中文。

日服渲染 jpText；国服补丁只改 enText。两者原始内容同键相同，
所以把中文 enText 拷进 jpText 就能生效。
"""
import os, json, zipfile, re
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(ROOT, 'dl/v15/tlw-payload-v1.5.zip')
KM = json.load(open(os.path.join(ROOT, 'lw_work/v15_keymatch.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'lw_work/ui_bridge')
os.makedirs(OUT, exist_ok=True)

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
tmp = os.path.join(OUT, '_cur.bundle')

zf = zipfile.ZipFile(ZIP)
made = []
total = 0

for r in KM['hit']:
    if r.get('kind') == 'font':
        continue
    try:
        data = zf.read('payload/' + r['file'])
    except Exception:
        continue
    open(tmp, 'wb').write(data)
    try:
        env = UnityPy.load(tmp)
    except Exception:
        continue
    parts = r['device_rel'].split('/')
    a, b = parts[1], parts[2]

    n = 0
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not isinstance(t, dict) or 'jpText' not in t:
            continue
        en = t.get('enText')
        if not isinstance(en, str) or not en.strip():
            continue
        if not HAN.search(en) or KANA.search(en):
            continue
        if t.get('jpText') == en:
            continue
        t['jpText'] = en
        # m_Text 也同步，避免部分界面读 m_Text
        if isinstance(t.get('m_Text'), str) and t['m_Text'].strip():
            t['m_Text'] = en
        o.save_typetree(t)
        n += 1

    if not n:
        continue
    dst = os.path.join(OUT, f'{a}__{b}__data')
    raw = env.file.save(packer='original')
    open(dst, 'wb').write(raw)
    total += n
    made.append({'a': a, 'b': b, 'fields': n, 'size': len(raw)})
    print(f'  {a[:10]}…  桥接 {n:>3} 字段  {os.path.getsize(tmp)} -> {len(raw)} B')

json.dump(made, open(os.path.join(ROOT, 'lw_work/ui_bridge_made.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n共 {len(made)} 个包、{total} 个字段 -> {OUT}')
