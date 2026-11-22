# -*- coding: utf-8 -*-
"""1) 找出含「ログイン/スタンプ/受け取り」等签到文字的 UI bundle
2) 对比设备上的 __data 与本地 clean 版本 md5，判断设备实际是哪一版
"""
import os, sys, re, json, hashlib, subprocess
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
SRC = os.path.join(ROOT, 'lw_work', 'jpuc3')

KEYS = ['ログイン', 'スタンプ', '受け取り', 'ログボ', '連続']

def sh(cmd):
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True,
                       encoding='utf-8', errors='replace')
    return ((r.stdout or '') + (r.stderr or '')).strip()

def md5b(b):
    return hashlib.md5(b).hexdigest()

hits = []
for a in sorted(os.listdir(SRC)):
    d = os.path.join(SRC, a)
    if not os.path.isdir(d):
        continue
    for b in os.listdir(d):
        fp = os.path.join(d, b, '__data')
        if not os.path.exists(fp):
            continue
        try:
            env = UnityPy.load(fp)
        except Exception:
            continue
        found = None
        for o in env.objects:
            if o.type.name != 'MonoBehaviour':
                continue
            try:
                t = o.read_typetree()
            except Exception:
                continue
            if not isinstance(t, dict):
                continue
            for k in ('jpText', 'm_text', 'm_Text'):
                v = t.get(k)
                if isinstance(v, str) and any(x in v for x in KEYS) and len(v) < 120:
                    found = v
                    break
            if found:
                break
        if found:
            hits.append((a, b, found))

print(f'含签到文字的 UI bundle: {len(hits)} 个')
for a, b, v in hits[:20]:
    # 设备 md5 vs 本地 clean
    clean_p = None
    for d in ('ui_out', 'ui_text_out'):
        p = os.path.join(ROOT, 'lw_work', d, f'{a}__{b}__data')
        if os.path.exists(p):
            clean_p = p
            break
    dev_md5 = sh(f"md5sum {UC}/{a}/{b}/__data 2>/dev/null").split(' ')[0]
    if clean_p:
        loc = md5b(open(clean_p, 'rb').read())
        flag = 'CLEAN已在设备' if dev_md5 == loc else 'A设备≠clean'
    else:
        flag = '无本地产物(未改)'
    print(f'  {a[:10]}/{b[:8]}  {flag}   {v[:40]!r}')
