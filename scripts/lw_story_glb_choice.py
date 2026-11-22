# -*- coding: utf-8 -*-
"""检查 v1.5 补丁（国际服汉化包）的 story 包：SelectOrder 选项是否已翻译。"""
import os, zipfile, re, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
ZIP = os.path.join(ROOT, 'dl/v15/tlw-payload-v1.5.zip')
KANA = re.compile(r'[\u3040-\u30ff]')
HAN = re.compile(r'[\u4e00-\u9fff]')
ASCII = re.compile(r'[A-Za-z]{2,}')

zf = zipfile.ZipFile(ZIP)
st = zf.namelist()
story_files = [n for n in st if n.startswith('payload/story/')]
print(f'v1.5 story 包 {len(story_files)} 个')

tmp = os.path.join(ROOT, 'lw_work', '_glb.bundle')
tot = 0
en = 0
ja = 0
cn = 0
samples = []
for i, n in enumerate(story_files):
    data = zf.read(n)
    open(tmp, 'wb').write(data)
    try:
        env = UnityPy.load(tmp)
    except Exception:
        continue
    cls = {}
    for o in env.objects:
        if o.type.name == 'MonoScript':
            try:
                cls[o.path_id] = getattr(o.read(), 'm_ClassName', '')
            except Exception:
                pass
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not isinstance(t, dict):
            continue
        sp = t.get('m_Script') or {}
        cn = cls.get(sp.get('m_PathID')) if isinstance(sp, dict) else None
        if cn != 'SelectOrder':
            continue
        for f in ('m_strfst', 'm_strsnd', 'm_str3rd'):
            v = t.get(f)
            if isinstance(v, str) and v.strip():
                tot += 1
                if ASCII.search(v) and not KANA.search(v) and not HAN.search(v):
                    en += 1
                    if len(samples) < 15:
                        samples.append(v[:50])
                elif KANA.search(v):
                    ja += 1
                elif HAN.search(v):
                    cn += 1
print(f'\nv1.5 补丁 SelectOrder 文本共 {tot} 条')
print(f'  英文 {en}, 日文 {ja}, 中文 {cn}')
print('英文样本:')
for s in samples:
    print(f'  {s!r}')
