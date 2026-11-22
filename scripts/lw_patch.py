#!/usr/bin/env python3
"""东方归言录 日服汉化 · 回写工具（把中文写进 master 表并推送到手机）

trans.json 格式（表名可用 lw_lookup.py names 查，也支持 32 位 hash）：
{
  "Mission":  {"110610": {"2": "通关「终幕」"}},
  "Chapter":  {"1001":   {"2": "序章　幻想乡的开幕"}}
}

用法：
  python lw_patch.py build trans.json              # 只生成加密文件到 out/
  python lw_patch.py build trans.json --push       # 生成并推送到手机（adb + su）
  python lw_patch.py build trans.json --push --pkg com.gg.lostword.mi
  python lw_patch.py verify out/Mission.bin        # 解密回来核对改了哪些字段

说明：
  * 只改 trans.json 里点名的字段，其余字段原样保留（字段类型/顺序不变）。
  * 加密 = AES-128-CBC/PKCS7，key/iv 见 lw_master.py（与游戏一致）。
"""
import os, sys, json, argparse, subprocess, msgpack

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lw_master import decrypt, encrypt

ROOT = os.path.dirname(os.path.abspath(__file__))
JP_DIR = os.path.join(ROOT, 'dumped')
OUT_DIR = os.path.join(ROOT, 'out')
ADB = os.path.join(ROOT, 'tools', 'platform-tools', 'adb.exe')
PKG = 'jp.goodsmile.touhoulostword_android'
CACHE = f'/data/data/{PKG}/files/cache'


def load_names():
    names = json.load(open(os.path.join(ROOT, 'lw_work', 'table_names.json'), encoding='utf-8'))
    return names


def resolve(spec):
    """表名 -> hash；也接受 hash 本身或 hash 前缀"""
    names = load_names()
    if spec in names:
        return names[spec], spec
    low = spec.lower()
    for n, h in names.items():
        if h == low or h.startswith(low):
            return h, n
    raise SystemExit(f'找不到表: {spec}')


def build(trans, out_dir=OUT_DIR, verbose=True):
    os.makedirs(out_dir, exist_ok=True)
    made = []
    manifest = {}
    mp = os.path.join(out_dir, '_manifest.json')
    if os.path.exists(mp):
        try:
            manifest = json.load(open(mp, encoding='utf-8'))
        except Exception:
            manifest = {}
    for table, entries in trans.items():
        h, name = resolve(table)
        src = os.path.join(JP_DIR, h + '.msgpack')
        if not os.path.exists(src):
            print(f'!! {name}: 日服无此表')
            continue
        obj = msgpack.unpackb(open(src, 'rb').read(), raw=False, strict_map_key=False)
        n = 0
        for k, fields in entries.items():
            key = int(k) if str(k).lstrip('-').isdigit() else k
            if key not in obj:
                print(f'!! {name}: 没有 id={k}，跳过')
                continue
            row = obj[key]
            for idx, text in fields.items():
                i = int(idx)
                if i >= len(row):
                    print(f'!! {name} id={k}: 字段 {i} 越界（共 {len(row)} 个），跳过')
                    continue
                if row[i] == text:
                    continue
                row[i] = text
                n += 1
        if not n:
            continue
        blob = msgpack.packb(obj, use_bin_type=True)
        enc = encrypt(blob)
        p = os.path.join(out_dir, name + '.bin')
        open(p, 'wb').write(enc)
        if verbose:
            print(f'{name:28} id 改动 {len(entries):>4} 条 · 字段 {n:>4} 个 · {len(enc)} 字节 -> {p}')
        made.append((name, h, p, n))
        manifest[name] = h
    if manifest:
        json.dump(manifest, open(os.path.join(out_dir, '_manifest.json'), 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
    return made


def push(made, pkg=PKG, adb=ADB):
    cache = f'/data/data/{pkg}/files/cache'
    for name, h, p, _ in made:
        remote = f'/sdcard/Download/{h}.patch'
        subprocess.run([adb, 'push', p, remote], check=True, stdout=subprocess.DEVNULL)
        cmd = f"su -c 'cp {remote} {cache}/{h}; chown u0_a469:u0_a469 {cache}/{h}; chmod 600 {cache}/{h}'"
        r = subprocess.run([adb, 'shell', cmd], capture_output=True, text=True)
        if r.returncode:
            print(f'{name}: 推送失败 {r.stderr.strip()}')
        else:
            print(f'{name}: 已推送 {h}')
    print('提示: 强制重启游戏才会重新读表 ——  adb shell su -c "am force-stop ' + pkg + '"')


def push_all(out_dir=OUT_DIR, pkg=PKG, adb=ADB):
    mp = os.path.join(out_dir, '_manifest.json')
    if not os.path.exists(mp):
        raise SystemExit(f'{mp} 不存在，先 build')
    manifest = json.load(open(mp, encoding='utf-8'))
    made = []
    for name, h in manifest.items():
        p = os.path.join(out_dir, name + '.bin')
        if os.path.exists(p):
            made.append((name, h, p, 0))
    print(f'推送 {len(made)} 张表...')
    push(made, pkg, adb)


def push_some(out_dir=OUT_DIR, pkg=PKG, adb=ADB, tables=()):
    mp = os.path.join(out_dir, '_manifest.json')
    manifest = json.load(open(mp, encoding='utf-8'))
    made = []
    for t in tables:
        h, name = resolve(t)
        p = os.path.join(out_dir, name + '.bin')
        if not os.path.exists(p):
            print(f'!! {name}.bin 不存在，先 build')
            continue
        made.append((name, h, p, 0))
    push(made, pkg, adb)


def verify(path):
    sys.path.insert(0, os.path.join(ROOT))
    from lw_lookup import NAME_OF
    raw = open(path, 'rb').read()
    obj = msgpack.unpackb(decrypt(raw), raw=False, strict_map_key=False)
    # 尝试找到同名原始表
    print(f'{os.path.basename(path)}: {len(obj)} 条记录，{len(raw)} 字节')
    return obj


def main():
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument('cmd')
    ap.add_argument('path', nargs='?')
    ap.add_argument('--push', action='store_true')
    ap.add_argument('--pkg', default=PKG)
    ap.add_argument('--out', default=OUT_DIR)
    a, _unknown = ap.parse_known_args()
    if a.cmd == 'build':
        trans = json.load(open(a.path, encoding='utf-8-sig'))
        made = build(trans, a.out)
        print(f'\n共 {len(made)} 张表、{sum(m[3] for m in made)} 个字段')
        if a.push:
            push(made, a.pkg)
    elif a.cmd == 'pushall':
        push_all(a.out, a.pkg)
    elif a.cmd == 'pushsome':
        extra = [x for x in sys.argv[2:] if not x.startswith('-')]
        push_some(a.out, a.pkg, ADB, extra)
    elif a.cmd == 'verify':
        verify(a.path)
    else:
        print(__doc__)


if __name__ == '__main__':
    main()
