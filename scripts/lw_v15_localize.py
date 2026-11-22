# -*- coding: utf-8 -*-
"""检查 v1.5 命中的界面包：LocalizeText 的 m_Text / enText / jpText 各是什么。

关键问题：国服补丁有没有把中文也写进 jpText？
  有  -> 日服可直接用（日服读 jpText）
  没有 -> 日服必须自己改 jpText
"""
import os, json, zipfile, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(ROOT, 'dl/v15/tlw-payload-v1.5.zip')
KM = json.load(open(os.path.join(ROOT, 'lw_work/v15_keymatch.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'lw_work/v15_localize_probe')

KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')

os.makedirs(OUT, exist_ok=True)
zf = zipfile.ZipFile(ZIP)

stats = collections.Counter()
rows = []
tmp = os.path.join(OUT, '_cur.bundle')

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
    key = f'{parts[1]}/{parts[2]}'
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not isinstance(t, dict):
            continue
        if not ({'enText', 'jpText'} & set(t.keys())):
            continue
        en, jp, mt = t.get('enText'), t.get('jpText'), t.get('m_Text')
        # 判断 jpText 是否已汉化：有汉字且无假名
        jp_sc = isinstance(jp, str) and jp.strip() and HAN.search(jp) and not KANA.search(jp)
        jp_ja = isinstance(jp, str) and jp.strip() and bool(KANA.search(jp))
        en_sc = isinstance(en, str) and en.strip() and HAN.search(en) and not KANA.search(en)
        stats['jpText_中文' if jp_sc else ('jpText_日文' if jp_ja else 'jpText_空/其他')] += 1
        stats['enText_中文' if en_sc else 'enText_其他'] += 1
        if jp_sc and len(rows) < 40:
            rows.append({'key': key, 'm_Text': mt, 'enText': en, 'jpText': jp,
                         'showingLanguage': t.get('showingLanguage')})

print('=== 国服界面包 LocalizeText 字段语言统计 ===')
for k, v in stats.most_common():
    print(f'  {k:16} {v}')

print('\n=== jpText 已是中文的样本 ===')
for r in rows[:20]:
    print(f'  [{r["key"][:10]}] lang={r["showingLanguage"]}')
    print(f'     m_Text={r["m_Text"]!r}')
    print(f'     enText={r["enText"]!r}')
    print(f'     jpText={r["jpText"]!r}')

json.dump(rows, open(os.path.join(ROOT, 'lw_work/v15_localize_rows.json'), 'w',
                     encoding='utf-8'), ensure_ascii=False, indent=1)
