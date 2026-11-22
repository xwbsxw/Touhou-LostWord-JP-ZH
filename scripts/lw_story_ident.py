# -*- coding: utf-8 -*-
"""识别 3 个剧情包属于哪个活动/章节，并对比重打包前后的 UnityFS 头部。"""
import os, re, struct, collections
import UnityPy

ROOT = os.path.dirname(os.path.abspath(__file__))
PAIRS = [
 ('3278c24fc3d882c7cbe884eac298a44d', '53fa0bfe9c0602ae527bec474d55f3aa'),
 ('580339df439f3804b452f0120b0854d0', 'f1b3616d93c0177db247fb42ae622dbf'),
 ('bd8d299435a553addd74a77bb5743c4f', '53de713efb322b975e00e391e1e00c59'),
]


def header(p):
    """解析 UnityFS 头部固定字段"""
    with open(p, 'rb') as f:
        sig = f.read(8)
        ver = struct.unpack('>I', f.read(4))[0]
        uver = f.read(1 + struct.unpack('>B', f.read(1))[0]) if False else None
        f.seek(12)
        # 读 C 字符串形式的 unityVersion / unityRevision
        def cstr():
            b = b''
            while True:
                c = f.read(1)
                if not c or c == b'\x00':
                    return b.decode('utf-8', 'replace')
                b += c
        uv = cstr()
        ur = cstr()
        size = struct.unpack('>q', f.read(8))[0]
        cisz = struct.unpack('>I', f.read(4))[0]
        uisz = struct.unpack('>I', f.read(4))[0]
        flags = struct.unpack('>I', f.read(4))[0]
    return dict(sig=sig, ver=ver, unity=uv, rev=ur, size=size,
                csize=cisz, usize=uisz, flags=hex(flags))


for a, b in PAIRS:
    src = os.path.join(ROOT, 'lw_work', 'jpuc', a, b, '__data')
    dst = os.path.join(ROOT, 'lw_work', 'story_out', f'{a}__{b}__data')
    print(f'=== {a[:10]} ===')
    h1, h2 = header(src), header(dst)
    for k in ('sig', 'ver', 'unity', 'rev', 'flags'):
        same = 'OK ' if h1[k] == h2[k] else '!! '
        print(f'  {same}{k}: {h1[k]}  ->  {h2[k]}')
    print(f'     compressed {h1["csize"]} -> {h2["csize"]}, '
          f'uncompressed {h1["usize"]} -> {h2["usize"]}')

    env = UnityPy.load(src)
    for o in env.objects:
        if o.type.name != 'AssetBundle':
            continue
        d = o.read()
        print(f'  资源包名: {getattr(d, "m_Name", "?")}')
        cont = getattr(d, 'm_Container', None) or []
        pref = collections.Counter()
        for k, _ in cont:
            m = re.match(r'assets/(.+?)/(?:[^/]+)$', k)
            pref[m.group(1) if m else k] += 1
        for p, c in pref.most_common(6):
            print(f'    {c:>5}  {p}')
        break
    print()
