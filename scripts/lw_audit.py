# -*- coding: utf-8 -*-
"""全面排查汉化产物（完整版，输出到文件）。"""
import os, sys, json, re, msgpack
import UnityPy
from opencc import OpenCC

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
from lw_master import decrypt

T2S = OpenCC('t2s')
KANA = re.compile(r'[\u3040-\u30ff]')
CJK = re.compile(r'[\u4e00-\u9fff]')

def is_trad(s):
    if not s or not CJK.search(s):
        return False
    return T2S.convert(s) != s

out_lines = []

def scan(name, texts):
    tr = ja = 0
    tr_s = []
    ja_s = []
    for loc, s in texts:
        if not isinstance(s, str) or not s.strip():
            continue
        if is_trad(s):
            tr += 1
            if len(tr_s) < 6:
                tr_s.append((loc, s[:50]))
        elif KANA.search(s):
            ja += 1
            if len(ja_s) < 6:
                ja_s.append((loc, s[:50]))
    return tr, ja, tr_s, ja_s

# 1. 主表
out_lines.append('========== 主表 out/ ==========')
tot_tr = tot_ja = 0
for fn in sorted(os.listdir(os.path.join(ROOT, 'out'))):
    if not fn.endswith('.bin'):
        continue
    try:
        obj = msgpack.unpackb(decrypt(open(os.path.join(ROOT, 'out', fn), 'rb').read()),
                              raw=False, strict_map_key=False)
    except Exception as e:
        out_lines.append(f'{fn}: 解密失败 {e}')
        continue
    texts = []
    for rid, row in obj.items():
        if isinstance(row, list):
            for i, v in enumerate(row):
                if isinstance(v, str):
                    texts.append((f'#{rid}[{i}]', v))
        elif isinstance(row, str):
            texts.append((f'#{rid}', row))
    tr, ja, tr_s, ja_s = scan(fn, texts)
    if tr or ja:
        out_lines.append(f'{fn}: 繁体 {tr}, 日文 {ja}')
        for loc, s in tr_s:
            out_lines.append(f'    [繁] {loc}: {s}')
        for loc, s in ja_s:
            out_lines.append(f'    [日] {loc}: {s}')
    tot_tr += tr; tot_ja += ja
out_lines.append(f'>>> 主表合计: 繁体 {tot_tr}, 日文 {tot_ja}')

# 2. 剧情包 story_sc_out
out_lines.append('\n========== 剧情包 story_sc_out ==========')
for fn in sorted(os.listdir(os.path.join(ROOT, 'lw_work', 'story_sc_out'))):
    if not fn.endswith('__data'):
        continue
    a, b, _ = fn.split('__')
    env = UnityPy.load(os.path.join(ROOT, 'lw_work', 'story_sc_out', fn))
    texts = []
    for o in env.objects:
        if o.type.name != 'MonoBehaviour':
            continue
        try:
            t = o.read_typetree()
        except Exception:
            continue
        if not isinstance(t, dict):
            continue
        for k in ('m_text', 'm_strfst', 'm_strsnd', 'm_str3rd'):
            v = t.get(k)
            if isinstance(v, str) and v.strip():
                texts.append((f'{o.path_id}.{k}', v))
    tr, ja, tr_s, ja_s = scan(a[:8], texts)
    if tr or ja:
        out_lines.append(f'{a[:10]}: 繁体 {tr}, 日文 {ja}')
        for loc, s in tr_s:
            out_lines.append(f'    [繁] {loc}: {s}')
        for loc, s in ja_s:
            out_lines.append(f'    [日] {loc}: {s}')

# 3. UI 包
out_lines.append('\n========== UI 包 ui_out + ui_text_out ==========')
for d in ('ui_out', 'ui_text_out'):
    p = os.path.join(ROOT, 'lw_work', d)
    if not os.path.isdir(p):
        continue
    for fn in sorted(os.listdir(p)):
        if not fn.endswith('__data'):
            continue
        env = UnityPy.load(os.path.join(p, fn))
        texts = []
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            for k, v in t.items():
                if isinstance(v, str) and v.strip() and k not in ('m_GameObject', 'm_Script'):
                    texts.append((f'{o.path_id}.{k}', v))
        tr, ja, tr_s, ja_s = scan(fn[:10], texts)
        if tr or ja:
            out_lines.append(f'{d}/{fn[:10]}: 繁体 {tr}, 日文 {ja}')
            for loc, s in tr_s[:4]:
                out_lines.append(f'    [繁] {loc}: {s}')
            for loc, s in ja_s[:4]:
                out_lines.append(f'    [日] {loc}: {s}')

open(os.path.join(ROOT, 'lw_work', 'audit_report.txt'), 'w',
     encoding='utf-8').write('\n'.join(out_lines))
print(f'报告已写入 lw_work/audit_report.txt，共 {len(out_lines)} 行')
