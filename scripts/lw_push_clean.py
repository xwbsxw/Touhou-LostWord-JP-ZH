# -*- coding: utf-8 -*-
"""免 root 推送干净 UI 包（利用重下后文件属组为 ext_data_rw、组可写）。

顺序：先 ui_out（LocalizeText.jpText），再 ui_text_out（在其基础上加 Text.m_Text）。
每推一个包就重写 __info（epoch = __data 的 mtime），保证 Unity 缓存有效。
"""
import os, sys, subprocess, hashlib

ROOT = os.path.dirname(os.path.abspath(__file__))
ADB = os.path.join(ROOT, 'adtools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
UC = f'/sdcard/Android/data/{PKG}/files/UnityCache/Shared'
TMP = '/data/local/tmp'


def sh(cmd):
    r = subprocess.run([ADB, 'shell', cmd], capture_output=True,
                       encoding='utf-8', errors='replace')
    return ((r.stdout or '') + (r.stderr or '')).strip()


def md5_local(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def push_dir(name, limit=None):
    p = os.path.join(ROOT, 'lw_work', name)
    if not os.path.isdir(p):
        return 0, 0
    files = sorted(f for f in os.listdir(p) if f.endswith('__data'))
    if limit:
        files = files[:limit]
    ok = bad = 0
    for fn in files:
        a, b, _ = fn.split('__')
        lp = os.path.join(p, fn)
        d = f'{UC}/{a}/{b}'
        rp = f'{TMP}/cl_{a}.bin'
        pr = subprocess.run([ADB, 'push', lp, rp], capture_output=True,
                            encoding='utf-8', errors='replace')
        if pr.returncode != 0:
            print(f'  {a[:10]}… push 失败')
            bad += 1
            continue
        out = sh(f'cp {rp} {d}/__data 2>&1 && rm -f {rp}')
        if 'denied' in out.lower():
            print(f'  {a[:10]}… 写入被拒: {out[:60]}')
            bad += 1
            continue
        info = sh(f'E=$(stat -c %Y {d}/__data) && '
                  f'printf -- "-1\\n%s\\n1\\n__data\\n" $E > {d}/__info && '
                  f'touch -d @$E {d}/__info && echo ok')
        got = sh(f'md5sum {d}/__data 2>/dev/null').split(' ')[0]
        if got == md5_local(lp):
            ok += 1
        else:
            bad += 1
            print(f'  {a[:10]}… MISMATCH (md5={got[:8]}) info={info[:30]}')
    return ok, bad


def main():
    limit = None
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])
    sh(f'am force-stop {PKG}')
    print('=== 推送 ui_out（jpText）===')
    o1, b1 = push_dir('ui_out', limit)
    print(f'  成功 {o1}, 失败 {b1}')
    print('=== 推送 ui_text_out（m_Text）===')
    o2, b2 = push_dir('ui_text_out', limit)
    print(f'  成功 {o2}, 失败 {b2}')
    print(f'\n合计成功 {o1 + o2}, 失败 {b1 + b2}')


if __name__ == '__main__':
    main()
