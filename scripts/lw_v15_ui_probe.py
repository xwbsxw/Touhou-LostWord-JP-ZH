# -*- coding: utf-8 -*-
"""从 v1.5 zip 里取出与日服同键的 61 个包，扫描其中是否含有目标界面文字。

判定依据：包里 MonoBehaviour 的字符串字段出现界面词（商店/同伴/绘札/…），
或出现日文原词（ショップ/仲間/絵札/…）。
结果是「哪些同键包承载界面文字」。
"""
import os, io, json, zipfile, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(ROOT, 'dl/v15/tlw-payload-v1.5.zip')
OUT = os.path.join(ROOT, 'lw_work/v15_ui_probe')
KM = json.load(open(os.path.join(ROOT, 'lw_work/v15_keymatch.json'), encoding='utf-8'))

CN_WORDS = ['商店', '同伴', '绘札', '设施', '课题', '祈愿', '好友', '图鉴',
            '素材', '传书', '公告', '菜单', '探索', '特设', '封印', '派遣']
JP_WORDS = ['ショップ', '仲間', '絵札', '施設', '課題', 'おいのり',
            'フレンド', '図鑑', '素材', '伝書', '告知', 'メニュー', '探索']

os.makedirs(OUT, exist_ok=True)


def walk_str(o, out):
    if isinstance(o, str):
        if o.strip():
            out.append(o)
    elif isinstance(o, dict):
        for k, v in o.items():
            if k in ('m_Script', 'm_GameObject'):
                continue
            walk_str(v, out)
    elif isinstance(o, (list, tuple)):
        for v in o:
            walk_str(v, out)


rows = []
zf = zipfile.ZipFile(ZIP)
for i, r in enumerate(KM['hit']):
    if r.get('kind') == 'font':
        continue
    try:
        data = zf.read('payload/' + r['file'])
    except Exception as e:
        print(f'  读取失败 {r["file"]}: {e}')
        continue
    tmp = os.path.join(OUT, '_cur.bundle')
    open(tmp, 'wb').write(data)
    try:
        env = UnityPy.load(tmp)
    except Exception:
        continue
    strs = []
    classes = collections.Counter()
    for o in env.objects:
        if o.type.name == 'MonoScript':
            try:
                classes[getattr(o.read(), 'm_ClassName', '')] += 1
            except Exception:
                pass
        elif o.type.name == 'MonoBehaviour':
            try:
                t = o.read_typetree()
            except Exception:
                continue
            walk_str(t, strs)
    cn_hits = sorted({w for w in CN_WORDS if any(w in s for s in strs)})
    jp_hits = sorted({w for w in JP_WORDS if any(w in s for s in strs)})
    if cn_hits or jp_hits:
        rel = r['device_rel']
        parts = rel.split('/')
        rows.append({
            'key': f'{parts[1]}/{parts[2]}',
            'file': r['file'],
            'size': r['size'],
            'cn_words': cn_hits,
            'jp_words': jp_hits,
            'nstr': len(strs),
        })
        print(f'  {parts[1][:10]}… {r["size"]:>9} B  中文词={cn_hits} 日文词={jp_hits} 字符串={len(strs)}')

json.dump(rows, open(os.path.join(ROOT, 'lw_work/v15_ui_keys.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)
print(f'\n扫描 {len(KM["hit"])} 个同键包，其中 {len(rows)} 个含界面词')
