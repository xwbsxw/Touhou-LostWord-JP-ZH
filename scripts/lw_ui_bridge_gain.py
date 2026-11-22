# -*- coding: utf-8 -*-
"""对 61 个同键界面包做 enText -> jpText 桥接，统计收益。

原理：日服渲染 jpText，国服补丁把中文写在 enText。
      同键代表原始内容一致，所以直接把中文 enText 拷进 jpText 即可生效。
"""
import os, json, zipfile, re, collections
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
stat = collections.Counter()
per = []

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
    n_ok = n_noz = n_kana = n_en = 0
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
            n_noz += 1
            continue
        if not HAN.search(en):
            n_en += 1            # enText 还是英文
            continue
        if KANA.search(en):
            n_kana += 1          # enText 里仍有假名，不可信
            continue
        n_ok += 1
    stat['可桥接'] += n_ok
    stat['enText为英文'] += n_en
    stat['含假名'] += n_kana
    stat['enText为空'] += n_noz
    if n_ok:
        per.append({'key': key, 'ok': n_ok, 'size': r['size']})
        print(f'  {key[:10]}…  可桥接 {n_ok:>4}  (英文 {n_en}, 假名 {n_kana}, 空 {n_noz})')

print('\n=== 汇总 ===')
for k, v in stat.most_common():
    print(f'  {k:14} {v}')
per.sort(key=lambda x: -x['ok'])
print(f'\n有收益的包 {len(per)} 个；前 10:')
for p in per[:10]:
    print(f"   {p['key'][:10]}…  {p['ok']:>4} 条")
json.dump(per, open(os.path.join(ROOT, 'lw_work/ui_bridge_gain.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
