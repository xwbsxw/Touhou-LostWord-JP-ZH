#!/usr/bin/env python3
"""东方归言录 日服 master 数据 解密/加密/回写 工具（已实机验证可用）

用法示例：
  python lw_master.py decrypt              # 把 dev_jp/cache/jpcache 里所有表解到 dumped/
  python lw_master.py apply trans.json     # 用 {表文件: {条目id: {字段索引: 中文}}} 回写并推送
"""
import os, sys, json, glob, subprocess
import msgpack
from Crypto.Cipher import AES

SECRET = 'jR3GTK6vR6gPz2MNA7hPiGEYbG6vBsMAS5jaretmHu4PS78zz3YcijFBM9yJha5HL7wn3DFYd4XaFNLB'
NAME = 'MasterMsgPack'


def gen_key_iv():
    def gen(name, secret, length, idx):
        nc = [ord(c) for c in name]
        sc = [ord(c) for c in secret]
        out = []
        for i in range(length):
            c1 = nc[i % len(nc)]
            c2 = sc[idx % len(sc)]
            out.append(chr((c1 ^ c2) & 0xFF))
            idx += (c1 & 0xFF)
        return ''.join(out), idx
    ks, i1 = gen(NAME, SECRET, 16, len(NAME))
    vs, _ = gen(NAME, SECRET, 16, i1)
    return ks.encode()[:16], vs.encode()[:16]


KEY, IV = gen_key_iv()


def decrypt(raw: bytes) -> bytes:
    pt = AES.new(KEY, AES.MODE_CBC, IV).decrypt(raw)
    p = pt[-1]
    if 1 <= p <= 16 and pt[-p:] == bytes([p]) * p:
        pt = pt[:-p]
    return pt


def encrypt(raw: bytes) -> bytes:
    pad = 16 - len(raw) % 16
    return AES.new(KEY, AES.MODE_CBC, IV).encrypt(raw + bytes([pad]) * pad)


def cmd_decrypt(src='dev_jp/cache/jpcache', dst='dumped'):
    os.makedirs(dst, exist_ok=True)
    ok = bad = 0
    for f in glob.glob(os.path.join(src, '*')):
        d = open(f, 'rb').read()
        if len(d) % 16 or d[:4] == b'EAST':
            continue
        try:
            pt = decrypt(d)
            msgpack.unpackb(pt, raw=False, strict_map_key=False)
        except Exception:
            bad += 1
            continue
        open(os.path.join(dst, os.path.basename(f) + '.msgpack'), 'wb').write(pt)
        ok += 1
    print(f'decrypted {ok}, skipped/failed {bad}')


def cmd_apply(trans_path, pkg='jp.goodsmile.touhoulostword_android'):
    """trans.json 形如 {"表文件名": {"1001": {"2": "第1章　幻想孤岛"}}}"""
    trans = json.load(open(trans_path, encoding='utf-8'))
    adb = sys.argv[4] if len(sys.argv) > 4 else 'tools/platform-tools/adb.exe'
    for table, entries in trans.items():
        src = f'dumped/{table}.msgpack'
        o = msgpack.unpackb(open(src, 'rb').read(), raw=False, strict_map_key=False)
        n = 0
        for k, fields in entries.items():
            key = int(k) if str(k).isdigit() else k
            if key not in o:
                continue
            row = o[key]
            for idx, text in fields.items():
                row[int(idx)] = text
                n += 1
        out = f'out_{table}.msgpack'
        open(out, 'wb').write(encrypt(msgpack.packb(o, use_bin_type=True)))
        subprocess.run([adb, 'push', out, f'/sdcard/Download/{out}'], check=True)
        cmd = (f"su -c 'cp /sdcard/Download/{out} /data/data/{pkg}/files/cache/{table}; "
               f"chown u0_a469:u0_a469 /data/data/{pkg}/files/cache/{table}; "
               f"chmod 600 /data/data/{pkg}/files/cache/{table}'")
        subprocess.run([adb, 'shell', cmd], check=True)
        print(f'{table}: {n} fields patched')


if __name__ == '__main__':
    if len(sys.argv) < 2 or sys.argv[1] == 'decrypt':
        cmd_decrypt()
    elif sys.argv[1] == 'apply':
        cmd_apply(sys.argv[2])
    else:
        print(__doc__)
